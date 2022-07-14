# Standard Library
import re
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Callable, Iterable, Optional

# Django
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.db import models, transaction
from django.db.models import Q
from django.db.models.query import QuerySet
from django.template import loader
from django.utils.timezone import make_aware
from django.utils.translation import gettext_lazy as _

# Third Party
import reversion
from django_fsm import FSMField, Transition, transition
from djmoney.models.fields import MoneyField
from model_utils.fields import MonitorField
from moneyed import Money
from polymorphic.models import PolymorphicModel
from taggit.managers import TaggableManager

# Locals
from .decorators import save_after
from .exceptions import BookingSlotIncorectService, BookingSlotMaxCustomers, BookingSlotMaxPets, BookingSlotOverlaps
from .utils import ChoicesEnum, choice_length


@reversion.register()
class Customer(models.Model):
    id: int
    pets: "QuerySet[Pet]"
    contacts: "QuerySet[Contact]"

    # Fields
    name = models.CharField(max_length=255)
    invoice_address = models.TextField(default="", blank=True)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    active = models.BooleanField(default=True)

    vet = models.ForeignKey(
        "crm.Vet",
        on_delete=models.SET_NULL,
        related_name="customers",
        blank=True,
        null=True,
        default=None,
    )

    tags = TaggableManager(blank=True)

    @property
    def active_pets(self):
        return self.pets.filter(active=True)

    @property
    def invoice_email(self):
        for contact in self.contacts.all():
            if contact.type == Contact.Type.EMAIL:
                return contact.details

        return None

    class Meta:
        ordering = ("-created",)

    def __str__(self) -> str:
        return f"{self.name}"

    @property
    def bookings(self):
        bookings = []

        for pet in self.pets.all():
            bookings.extend(pet.bookings.all())

        return bookings


@reversion.register()
class Pet(models.Model):
    bookings: "QuerySet[Booking]"

    class Social(models.TextChoices):
        YES = "yes", _("Yes")
        NO = "no", _("No")
        ANNON = "annon", _("Anonymous")

    class Neutered(models.TextChoices):
        YES = "yes", _("Yes")
        NO = "no", _("No")
        IMPLANT = "implant", _("Implant")
        __empty__ = _("(Unknown)")

    class Sex(models.TextChoices):
        MALE = "male", _("Male")
        FEMALE = "female", _("Female")
        __empty__ = _("(Unknown)")

    # Fields
    name = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    dob = models.DateField(blank=True, null=True)
    active = models.BooleanField(default=True)
    social_media_concent = models.CharField(default=Social.YES, choices=Social.choices, max_length=choice_length(Social))
    sex = models.CharField(null=True, default=None, choices=Sex.choices, max_length=choice_length(Sex))
    description = models.TextField(blank=True, default="")
    neutered = models.CharField(null=True, default=None, choices=Neutered.choices, max_length=choice_length(Neutered))
    medical_conditions = models.TextField(blank=True, default="")
    treatment_limit = models.IntegerField(default=0)
    allergies = models.TextField(blank=True, default="")

    tags = TaggableManager()

    # Relationship Fields
    customer = models.ForeignKey(
        "crm.Customer",
        on_delete=models.PROTECT,
        related_name="pets",
    )
    vet = models.ForeignKey(
        "crm.Vet",
        on_delete=models.SET_NULL,
        related_name="pets",
        blank=True,
        null=True,
        default=None,
    )

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return f"{self.name}"


@reversion.register()
class Vet(models.Model):
    # Fields
    name = models.CharField(max_length=255)
    phone = models.CharField(blank=True, null=True, max_length=128)
    details = models.TextField(blank=True, default="")
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return f"{self.name}"


@reversion.register()
class Contact(models.Model):
    class Type(Enum):
        PHONE = _("phone")
        MOBILE = _("mobile")
        EMAIL = _("email")
        UNKNOWN = _("unknown")

    EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")
    MOBILE_REGEX = re.compile(r"^(\+447|\(?07)[0-9\(\)\s]+$")
    PHONE_REGEX = re.compile(r"^\+?[0-9\(\)\s]+$")

    # Fields
    name = models.CharField(max_length=255)
    details = models.CharField(max_length=255, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)

    # Relationship Fields
    customer = models.ForeignKey(
        "crm.Customer",
        on_delete=models.CASCADE,
        related_name="contacts",
    )

    @property
    def type(self) -> Type:
        if self.EMAIL_REGEX.match(self.details):
            return self.Type.EMAIL

        if self.MOBILE_REGEX.match(self.details):
            return self.Type.MOBILE

        if self.PHONE_REGEX.match(self.details):
            return self.Type.PHONE

        return self.Type.UNKNOWN

    class Meta:
        ordering = ("-created",)
        unique_together = ("name", "customer")

    def __str__(self) -> str:
        return f"{self.name}"


def get_default_due_date() -> datetime:
    return datetime.now() + timedelta(weeks=1)


@reversion.register()
class Charge(PolymorphicModel):
    class States(ChoicesEnum):
        UNPAID = "unpaid"
        PAID = "paid"
        VOID = "void"
        REFUNDED = "refunded"

    id: int
    get_all_state_transitions: Callable[[], Iterable[Transition]]
    get_available_state_transitions: Callable[[], Iterable[Transition]]

    # Fields
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)

    name = models.CharField(max_length=255)
    line = MoneyField(max_digits=14, decimal_places=2, default_currency="GBP")
    quantity = models.IntegerField(default=1)

    state = FSMField(default=States.UNPAID.value, choices=States.choices(), protected=True)
    paid_on = MonitorField(monitor="state", when=[States.PAID.value], default=None, null=True)

    customer = models.ForeignKey(
        "crm.Customer",
        on_delete=models.SET_NULL,
        null=True,
        related_name="charges",
    )

    invoice = models.ForeignKey(
        "crm.Invoice",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="charges",
    )

    class Meta:
        ordering = ("-created",)

    def __str__(self) -> str:
        return f"{self.name} - {self.cost}"

    def __float__(self) -> float:
        return float(self.charge)

    def __add__(self, other) -> Money:
        if not isinstance(other, Charge):
            return NotImplemented
        return self.cost + other.cost

    @property
    def cost(self):
        return self.line * self.quantity

    @save_after
    @transition(field=state, source=States.UNPAID.value, target=States.PAID.value)
    def pay(self):
        pass

    @save_after
    @transition(field=state, source=States.UNPAID.value, target=States.VOID.value)
    def void(self) -> None:
        pass

    @save_after
    @transition(field=state, source=States.PAID.value, target=States.REFUNDED.value)
    def refund(self) -> None:
        pass

    def delete(self) -> None:
        return self.void()

    def save(self, *args, **kwargs):
        if self.customer is None and self.invoice is not None:
            self.customer = self.invoice.customer

        return super().save(*args, **kwargs)


class Invoice(models.Model):
    charges: models.QuerySet["Charge"]
    get_available_state_transitions: Callable[[], Iterable[Transition]]

    class States(ChoicesEnum):
        DRAFT = "draft"
        UNPAID = "unpaid"
        PAID = "paid"
        VOID = "void"

    details = models.TextField(blank=True, default="")
    due = models.DateField(blank=True, null=True, default=None)
    adjustment = MoneyField(default=0, max_digits=14, decimal_places=2, default_currency="GBP")

    customer_name = models.CharField(max_length=255, blank=True, null=True)
    sent_to = models.CharField(max_length=255, blank=True, null=True)

    state = FSMField(default=States.DRAFT.value, choices=States.choices(), protected=True)
    paid_on = MonitorField(monitor="state", when=[States.PAID.value], default=None, null=True)
    sent_on = MonitorField(monitor="state", when=[States.UNPAID.value], default=None, null=True)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)

    customer = models.ForeignKey(
        "crm.Customer",
        on_delete=models.SET_NULL,
        null=True,
        related_name="invoices",
    )

    def __str__(self) -> str:
        return self.name

    def can_send(self) -> bool:
        return self.customer is not None and self.customer.invoice_email is not None

    @property
    def can_edit(self) -> bool:
        return self.state == self.States.DRAFT.value

    @property
    def name(self) -> str:
        return f"INV-{self.pk:03}"

    @property
    def overdue(self) -> bool:
        return self.due is not None and self.due < date.today()

    @property
    def subtotal(self) -> float:
        return sum(c.cost for c in self.charges.all())

    @property
    def total(self) -> float:
        return self.subtotal + self.adjustment

    @property
    def total_unpaid(self) -> float:
        return sum(c.cost for c in self.charges.all() if c.state == c.States.UNPAID.value) + self.adjustment

    @save_after
    @transition(
        field=state,
        source=States.DRAFT.value,
        target=States.UNPAID.value,
        conditions=[can_send],
    )
    def send(self, to=None):
        self.customer_name = self.customer.name
        self.sent_to = to
        if self.due is None:
            self.due = date.today() + timedelta(weeks=1)

        self.send_email()

    def send_email(self):
        assert self.can_send(), "Unable to send email"

        template = loader.get_template("emails/invoice.html")
        context = {
            "invoice": self,
            "customer": self.customer,
        }

        email = EmailMultiAlternatives(
            f"Invoice {self.name} - Stretch there legs",
            "Message",
            "admin@stretchtheirlegs.co.uk",
            [self.customer.invoice_email],
        )

        email.attach_alternative(template.render(context), "text/html")
        # email.attach()

        return email.send()

    @save_after
    @transition(field=state, source=States.UNPAID.value, target=States.PAID.value)
    def pay(self):
        for charge in self.charges.all():
            charge.pay()

    @save_after
    @transition(field=state, source=(States.DRAFT.value, States.UNPAID.value), target=States.VOID.value)
    def void(self) -> None:
        pass

    def delete(self, using=None, keep_parents=False) -> None:
        if self.state == self.States.DRAFT.value:
            super().delete(using=using, keep_parents=keep_parents)
        else:
            self.void()

    @property
    def available_state_transitions(self) -> list[str]:
        return [i.name for i in self.get_available_state_transitions()]

    @property
    def issued(self):
        return self.sent_on or self.created


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
    def get_slot(cls, start: datetime, end: datetime) -> "BookingSlot":
        try:
            slot = cls.objects.get(start=start, end=end)
        except cls.DoesNotExist:
            slot = cls(start=start, end=end)

        return slot

    @staticmethod
    def round_date_time(dt: datetime) -> datetime:
        dt = dt - timedelta(minutes=dt.minute % 10, seconds=dt.second, microseconds=dt.microsecond)

        return make_aware(dt)

    def __str__(self) -> str:
        return f"{self.id}: {self.start} - {self.end}"

    def _valid_dates(self) -> bool:
        return self.end > self.start

    def get_overlapping(self) -> "QuerySet[BookingSlot]":
        start = Q(start__lt=self.start, end__gt=self.start)
        end = Q(start__lt=self.end, end__gt=self.end)
        equal = Q(start=self.start, end=self.end)

        return self.__class__.objects.filter(start | end | equal).exclude(pk=self.pk)

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
    def clean_empty_slots(cls):
        cls.objects.filter(bookings__isnull=True).delete()

    @property
    def service(self) -> Optional["Service"]:
        try:
            return self.bookings.all()[0].service
        except IndexError:
            return None

    @property
    def pets(self) -> set[Pet]:
        return {b.pet for b in self.bookings.all()}

    @property
    def pet_count(self) -> int:
        return len(self.pets)

    @property
    def customers(self) -> set[Customer]:
        return {b.pet.customer for b in self.bookings.all()}

    @property
    def customer_count(self) -> int:
        return len(self.customers)


@reversion.register()
class Booking(models.Model):
    class States(ChoicesEnum):
        ENQUIRY = "enquiry"
        PRELIMINARY = "preliminary"
        CONFIRMED = "confirmed"
        CANCELED = "canceled"
        COMPLETED = "completed"

    STATES_MOVEABLE = [States.ENQUIRY.value, States.PRELIMINARY.value, States.CONFIRMED.value]
    STATES_CANCELABLE = [States.ENQUIRY.value, States.PRELIMINARY.value, States.CONFIRMED.value]

    id: int
    get_all_state_transitions: Callable[[], Iterable[Transition]]
    get_available_state_transitions: Callable[[], Iterable[Transition]]

    # Fields
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    name = models.CharField(max_length=255)
    cost = models.PositiveIntegerField()
    start = models.DateTimeField()
    end = models.DateTimeField()

    state = FSMField(default=States.PRELIMINARY.value, choices=States.choices(), protected=True)

    # Relationship Fields
    pet = models.ForeignKey("crm.Pet", on_delete=models.PROTECT, related_name="bookings")
    service = models.ForeignKey("crm.Service", on_delete=models.PROTECT, related_name="bookings")
    booking_slot = models.ForeignKey("crm.BookingSlot", on_delete=models.PROTECT, related_name="bookings")

    charges = GenericRelation(Charge)

    class Meta:
        ordering = ("-created",)

    def __str__(self) -> str:
        return f"{self.start} - {self.end}"

    def save(self, *args, **kwargs) -> None:
        self.name = f"{self.pet.name} {self.service.name}"

        if self.pk is None:
            self.booking_slot = self._get_new_booking_slot()

        with transaction.atomic():
            if self.booking_slot is not None:
                self.booking_slot.save()

            super().save(*args, **kwargs)

    def create_charge(self) -> Charge:
        charge = BookingCharge(
            name=f"Charge for {self.name}",
            cost=self.cost,
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

        self.booking_slot = self._get_new_booking_slot()

        self.save()
        return True

    @save_after
    @transition(field=state, source=States.ENQUIRY.value, target=States.PRELIMINARY.value)
    def process(self) -> None:
        pass

    @save_after
    @transition(field=state, source=States.PRELIMINARY.value, target=States.CONFIRMED.value)
    def confirm(self) -> None:
        pass

    @save_after
    @transition(field=state, source=STATES_CANCELABLE, target=States.CANCELED.value)
    def cancel(self) -> None:
        self.booking_slot = None

    @save_after
    @transition(field=state, source=States.CANCELED.value, target=States.ENQUIRY.value)
    def reopen(self) -> None:
        self.booking_slot = self._get_new_booking_slot()

    @save_after
    @transition(field=state, source=States.CONFIRMED.value, target=States.COMPLETED.value, conditions=[can_complete])
    def complete(self) -> Charge:
        return self.create_charge()

    @property
    def available_state_transitions(self) -> list[str]:
        return [i.name for i in self.get_available_state_transitions()]


class BookingCharge(Charge):
    booking = models.ForeignKey(Booking, on_delete=models.PROTECT)


@reversion.register()
class Service(models.Model):
    # Fields
    name = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    length = models.DurationField(default=timedelta(minutes=60))
    booked_length = models.DurationField(default=timedelta(minutes=120))
    cost = MoneyField(max_digits=14, decimal_places=2, default_currency="GBP")
    cost_per_additional = MoneyField(max_digits=14, decimal_places=2, default_currency="GBP", default=0)
    max_pet = models.IntegerField(default=1)
    max_customer = models.IntegerField(default=1)
    display_colour = models.CharField(max_length=255)  # ColorField(default="#000000")

    class Meta:
        ordering = ("-created",)

    def __str__(self) -> str:
        return f"{self.name}"


@reversion.register()
class Address(models.Model):
    # Fields
    name = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    address_line_1 = models.CharField(max_length=100, blank=True, default="")
    address_line_2 = models.CharField(max_length=100, blank=True, default="")
    address_line_3 = models.CharField(max_length=100, blank=True, default="")
    town = models.CharField(max_length=100, blank=True, default="")
    county = models.CharField(max_length=100, blank=True, default="")
    postcode = models.CharField(max_length=100, blank=True, default="")

    # Relationship Fields
    customer = models.ForeignKey(
        "crm.Customer",
        on_delete=models.CASCADE,
        related_name="addresses",
    )

    class Meta:
        ordering = ("-created",)

    def __str__(self) -> str:
        return f"{self.name}"
