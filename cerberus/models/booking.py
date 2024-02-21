# Standard Library
from collections.abc import Callable, Iterable
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Self

# Django
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q
from django.db.models.query import QuerySet
from django.utils.timezone import make_aware

# Third Party
import reversion
from django_fsm import FSMField, Transition, transition
from humanize import naturaldate

# Locals
from ..decorators import save_after
from ..exceptions import BookingSlotIncorectService, BookingSlotMaxCustomers, BookingSlotMaxPets, BookingSlotOverlaps
from .charge import Charge

if TYPE_CHECKING:
    # Locals
    from . import Customer, Pet, Service


class BookingSlot(models.Model):
    id: int
    bookings: models.QuerySet["Booking"]

    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    start = models.DateTimeField()
    end = models.DateTimeField()

    class Meta:
        unique_together = [["start", "end"]]

    @classmethod
    def get_slot(cls, start: datetime, end: datetime) -> Self:
        try:
            slot = cls.objects.get(start=start, end=end)
        except cls.DoesNotExist:
            slot = cls(start=start, end=end)
            slot.save()

        return slot

    @staticmethod
    def round_date_time(dt: datetime) -> datetime:
        dt = dt - timedelta(minutes=dt.minute % 10, seconds=dt.second, microseconds=dt.microsecond)

        return make_aware(dt)

    def __str__(self) -> str:
        return f"{self.id}: {self.start} - {self.end}"

    def _valid_dates(self) -> bool:
        return self.end > self.start

    def get_overlapping(self) -> QuerySet[Self]:
        start = Q(start__lt=self.start, end__gt=self.start)
        end = Q(start__lt=self.end, end__gt=self.end)
        equal = Q(start=self.start, end=self.end)

        return self.__class__.objects.filter(start | end | equal).exclude(pk=self.pk)  # type: ignore

    def overlaps(self) -> bool:
        others = self.get_overlapping()

        return any(o.bookings.all().count() > 0 for o in others)

    def clean(self) -> None:
        if not self._valid_dates():
            raise ValidationError("end can not be before start")

        print(f"Checking for other slots between {self.start} and {self.end}")
        if self.overlaps():
            raise ValidationError(f"{self.__class__.__name__} overlaps another {self.__class__.__name__}")

    def move_slot(self, start: datetime, end: datetime | None = None) -> bool:
        if not all(b.can_move for b in self.bookings.all()):
            return False

        self.start = start
        self.end = start + (self.end - self.start) if end is None else end

        if self.overlaps():
            raise ValidationError("Slot overlaps another slot")

        with transaction.atomic():
            self.save()
            for booking in self.bookings.all():
                booking.start = self.start
                booking.end = self.end
                booking.save()

        return True

    def contains_all(self, bookingIDs: list[int]) -> bool:
        ids = [b.id for b in self.bookings.all()]
        return all(id in ids for id in bookingIDs)

    @classmethod
    def clean_empty_slots(cls) -> None:
        cls.objects.filter(bookings__isnull=True).delete()

    @property
    def service(self) -> "Service | None":
        try:
            return self.bookings.all()[0].service
        except IndexError:
            return None

    @property
    def pets(self) -> set["Pet"]:
        return {b.pet for b in self.bookings.all()}

    @property
    def pet_count(self) -> int:
        return len(self.pets)

    @property
    def customers(self) -> set["Customer"]:
        return {b.pet.customer for b in self.bookings.all()}

    @property
    def customer_count(self) -> int:
        return len(self.customers)


@reversion.register()
class Booking(models.Model):
    class States(models.TextChoices):
        ENQUIRY = "enquiry"
        PRELIMINARY = "preliminary"
        CONFIRMED = "confirmed"
        CANCELED = "canceled"
        COMPLETED = "completed"

    STATES_MOVEABLE: list[str] = [States.ENQUIRY.value, States.PRELIMINARY.value, States.CONFIRMED.value]
    STATES_CANCELABLE: list[str] = [States.ENQUIRY.value, States.PRELIMINARY.value, States.CONFIRMED.value]

    id: int
    get_all_state_transitions: Callable[[], Iterable[Transition]]
    get_available_state_transitions: Callable[[], Iterable[Transition]]

    # Fields
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    name = models.CharField(max_length=520)
    cost = models.PositiveIntegerField()
    start = models.DateTimeField()
    end = models.DateTimeField()

    state = FSMField(default=States.PRELIMINARY.value, choices=States.choices, protected=True)  # type: ignore

    # Relationship Fields
    pet = models.ForeignKey("cerberus.Pet", on_delete=models.PROTECT, related_name="bookings")
    service = models.ForeignKey("cerberus.Service", on_delete=models.PROTECT, related_name="bookings")
    _booking_slot = models.ForeignKey("cerberus.BookingSlot", on_delete=models.PROTECT, related_name="bookings")
    _booking_slot_id: int | None

    charges = GenericRelation(Charge)

    class Meta:
        ordering = ("-created",)

    def __str__(self) -> str:
        return f"{self.name} - {naturaldate(self.start)}"

    @property
    def length(self) -> timedelta:
        return self.end - self.start

    @property
    def booking_slot(self) -> BookingSlot:
        if self._booking_slot is None:
            if self.state == self.States.CANCELED.value:
                raise (BookingSlot.DoesNotExist("Booking has been canceled"))
            self._booking_slot = self._get_new_booking_slot()
        return self._booking_slot

    @booking_slot.setter
    def booking_slot(self, value: BookingSlot) -> None:
        self._booking_slot = value

    def save(self, *args, **kwargs) -> None:
        self.name = f"{self.pet.name}, {self.service.name}"

        with transaction.atomic():
            if self.pk is None and getattr(self, "_booking_slot", None) is None:
                self._booking_slot = self._get_new_booking_slot()

            if self._booking_slot is not None:
                self._booking_slot.save()

            super().save(*args, **kwargs)

    def create_charge(self) -> Charge:
        charge = BookingCharge(
            name=f"Charge for {self.name}"[:255],
            line=self.cost,
            booking=self,
            customer=self.pet.customer,
        )
        charge.save()

        return charge

    def _get_new_booking_slot(self) -> BookingSlot:
        slot = BookingSlot.get_slot(self.start, self.end)

        if slot.service != self.service and slot.service is not None:
            raise BookingSlotIncorectService("Incorect Service")

        if slot.customer_count >= self.service.max_customer and self.pet.customer not in slot.customers:
            raise BookingSlotMaxCustomers("Max customers")

        if slot.pet_count >= self.service.max_pet:
            raise BookingSlotMaxPets("Max pets")

        if slot.overlaps():
            overlaps = slot.get_overlapping()

            if not all(all(b.id == self.id for b in o.bookings.all()) for o in overlaps):
                raise BookingSlotOverlaps("Overlaps another slot")

        return slot

    @property
    def can_move(self) -> bool:
        return self.state in self.STATES_MOVEABLE

    def can_complete(self) -> bool:
        return self.end < make_aware(datetime.now())

    def move_booking(self, to: datetime) -> bool:
        if not self.can_move:
            return False

        delta = self.start - to
        self.start -= delta
        self.end -= delta

        self._booking_slot = self._get_new_booking_slot()

        self.save()
        return True

    def move_booking_slot(self, start: datetime) -> bool:
        if slot := self._booking_slot:
            length = slot.end - slot.start
            return slot.move_slot(start, start + length)

        return False

    @save_after
    @transition(field=state, source=States.ENQUIRY.value, target=States.PRELIMINARY.value)
    def process(self) -> None:
        pass

    @save_after
    @transition(field=state, source=States.PRELIMINARY.value, target=States.CONFIRMED.value)
    def confirm(self) -> None:
        pass

    @save_after
    @transition(field=state, source=STATES_CANCELABLE, target=States.CANCELED.value)  # type: ignore
    def cancel(self) -> None:
        self._booking_slot = None

    @save_after
    @transition(field=state, source=States.CANCELED.value, target=States.ENQUIRY.value)
    def reopen(self) -> None:
        self._booking_slot = self._get_new_booking_slot()

    @save_after
    @transition(field=state, source=States.CONFIRMED.value, target=States.COMPLETED.value, conditions=[can_complete])
    def complete(self) -> Charge:
        return self.create_charge()

    @property
    def available_state_transitions(self) -> list[str]:
        return [i.name for i in self.get_available_state_transitions()]


class BookingCharge(Charge):
    booking = models.ForeignKey(Booking, on_delete=models.PROTECT)
