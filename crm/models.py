# Standard Library
import re
from datetime import datetime, timedelta

# Django
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q
from django.utils.timezone import make_aware
from django.utils.translation import gettext_lazy as _

# Third Party
import reversion
from django_fsm import FSMField, transition

# Locals
from .exceptions import BookingSlotIncorectService, BookingSlotMaxCustomers, BookingSlotMaxPets, BookingSlotOverlaps


@reversion.register()
class Customer(models.Model):
    # Fields
    name = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    active = models.BooleanField(default=True)

    vet = models.ForeignKey(
        "cerberus.Vet",
        on_delete=models.CASCADE,
        related_name="customers",
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ("-created",)

    def __str__(self):
        return f"{self.name}"


@reversion.register()
class Pet(models.Model):
    class SocialMedia(models.TextChoices):
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
    social_media_concent = models.CharField(default=SocialMedia.YES, choices=SocialMedia.choices, max_length=5)
    sex = models.CharField(
        default=Sex.__empty__,
        choices=Sex.choices,
        max_length=10,
    )
    description = models.TextField(blank=True, default="")
    neutered = models.CharField(
        default=Neutered.__empty__,
        choices=Neutered.choices,
        max_length=10,
    )
    medical_conditions = models.TextField(blank=True, default="")
    treatment_limit = models.IntegerField(default=0)
    allergies = models.TextField(blank=True, default="")
    microchipped = models.BooleanField(default=True)
    off_lead_consent = models.BooleanField(default=False)
    vaccinated = models.BooleanField(default=True)
    flead_wormed = models.BooleanField(default=False)
    insured = models.BooleanField(default=False)
    leucillin = models.BooleanField(default=True)
    noise_sensitive = models.BooleanField(default=False)

    # Relationship Fields
    customer = models.ForeignKey(
        "cerberus.Customer",
        on_delete=models.CASCADE,
        related_name="pets",
    )
    vet = models.ForeignKey(
        "cerberus.Vet",
        on_delete=models.CASCADE,
        related_name="pets",
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return f"{self.name}"


@reversion.register()
class Vet(models.Model):
    # Fields
    name = models.CharField(max_length=255)
    phone = models.CharField(blank=True, null=True)
    details = models.TextField(blank=True, default="")
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return f"{self.name}"


@reversion.register()
class Contact(models.Model):
    PHONE = "phone"
    MOBILE = "mobile"
    EMAIL = "email"
    UNKNOWN = "unknown"

    EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")

    # Fields
    name = models.CharField(max_length=255)
    details = models.CharField(max_length=255, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)

    # Relationship Fields
    customer = models.ForeignKey(
        "cerberus.Customer",
        on_delete=models.CASCADE,
        related_name="contacts",
    )

    class Meta:
        ordering = ("-created",)

    class graphql:
        extra_fields = ["contactType"]

    def __str__(self):
        return f"{self.name}"


def get_default_due_date():
    return datetime.now() + timedelta(weeks=1)


@reversion.register()
class Charge(models.Model):
    STATE_UNCONFIRMED = "unconfirmed"
    STATE_UNPAID = "unpaid"
    STATE_OVERDUE = "overdue"
    STATE_PAID = "paid"
    STATE_VOID = "void"

    STATES = [STATE_UNCONFIRMED, STATE_UNPAID, STATE_OVERDUE, STATE_PAID, STATE_VOID]

    # Fields
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)

    name = models.CharField(max_length=255)
    cost = models.IntegerField()
    due = models.DateTimeField(default=get_default_due_date)

    state = FSMField(default=STATE_UNPAID, choices=list(zip(STATES, STATES)), protected=True)

    customer = models.ForeignKey("cerberus.Customer", on_delete=models.SET_NULL, null=True)
    booking = models.ForeignKey("cerberus.Booking", on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        ordering = ("-created",)

    def __str__(self) -> str:
        return f"£{self.cost / 100:.2f}"

    @transition(field=state, source=STATE_UNCONFIRMED, target=STATE_UNPAID)
    def confirm(self):
        pass

    @transition(field=state, source=[STATE_UNPAID, STATE_OVERDUE], target=STATE_PAID)
    def paid(self):
        pass

    @transition(field=state, source=STATE_UNPAID, target=STATE_OVERDUE)
    def overdue(self):
        pass

    @transition(field=state, source=[STATE_UNPAID, STATE_OVERDUE], target=STATE_VOID)
    def void(self):
        pass


class BookingSlot(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    start = models.DateTimeField()
    end = models.DateTimeField()

    class Meta:
        unique_together = [["start", "end"]]

    @classmethod
    def getSlot(cls, start, end):
        try:
            slot = cls.objects.get(start=start, end=end)
        except cls.DoesNotExist:
            slot = cls(start=start, end=end)

        return slot

    @staticmethod
    def roundDateTime(dt):
        dt = dt - timedelta(minutes=dt.minute % 10, seconds=dt.second, microseconds=dt.microsecond)

        return make_aware(dt)

    def __str__(self) -> str:
        return f"{self.id}: {self.start} - {self.end}"

    def _validDates(self) -> bool:
        return self.end > self.start

    def getOverlapping(self):
        start = Q(start__lt=self.start, end__gt=self.start)
        end = Q(start__lt=self.end, end__gt=self.end)
        equal = Q(start=self.start, end=self.end)

        return self.__class__.objects.filter(start | end | equal).exclude(pk=self.pk)

    def overlaps(self) -> bool:
        others = self.getOverlapping()

        return any(o.bookings.all().count() > 0 for o in others)

    def clean(self):
        if not self._validDates():
            raise ValidationError("end can not be before start")

        print(f"Checking for other slots between {self.start} and {self.end}")
        if self.overlaps():
            raise ValidationError(f"{self.__class__.__name__} overlaps another {self.__class__.__name__}")

    def moveSlot(self, start, end=None):
        if not all(b.canMove for b in self.bookings.all()):
            return

        if end is None:
            end = start + (self.end - self.start)

        self.start = start
        self.end = end

        if self.overlaps():
            raise ValidationError("Slot overlaps another slot")

        with transaction.atomic():
            self.save()
            for booking in self.bookings.all():
                booking.start = self.start
                booking.end = self.end
                booking.save()

    def containsAll(self, bookingIDs):
        ids = [b.id for b in self.bookings.all()]
        return all(id in ids for id in bookingIDs)

    @classmethod
    def cleanEmptySlots(cls):
        cls.objects.filter(bookings__isnull=True).delete()

    @property
    def service(self):
        try:
            return self.bookings.all()[0].service
        except IndexError:
            return None

    @property
    def pets(self):
        return {b.pet for b in self.bookings.all()}

    @property
    def pet_count(self):
        return len(self.pets)

    @property
    def customers(self):
        return {b.pet.customer for b in self.bookings.all()}

    @property
    def customer_count(self):
        return len(self.customers)


@reversion.register()
class Booking(models.Model):
    STATE_ENQUIRY = "enquiry"
    STATE_PRELIMINARY = "preliminary"
    STATE_CONFIRMED = "confirmed"
    STATE_CANCELED = "canceled"
    STATE_COMPLETED = "completed"

    STATES = [STATE_ENQUIRY, STATE_PRELIMINARY, STATE_CONFIRMED, STATE_CANCELED, STATE_COMPLETED]
    STATES_MOVEABLE = [STATE_ENQUIRY, STATE_PRELIMINARY, STATE_CONFIRMED]

    # Fields
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    name = models.CharField(max_length=255)
    cost = models.IntegerField()
    start = models.DateTimeField()
    end = models.DateTimeField()

    state = FSMField(default=STATE_PRELIMINARY, choices=list(zip(STATES, STATES)), protected=True)

    # Relationship Fields
    pet = models.ForeignKey("cerberus.Pet", on_delete=models.SET_NULL, related_name="bookings", blank=True, null=True)
    service = models.ForeignKey("cerberus.Service", on_delete=models.SET_NULL, related_name="bookings", blank=True, null=True)
    booking_slot = models.ForeignKey(
        "cerberus.BookingSlot", on_delete=models.SET_NULL, related_name="bookings", blank=True, null=True
    )

    class Meta:
        ordering = ("-created",)

    def __str__(self):
        return f"{self.start} - {self.end}"

    def save(self, *args, **kwargs):
        self.name = f"{self.pet.name} {self.service.name}"

        if self.pk is None:
            self.booking_slot = self._getNewBookingSlot()

        with transaction.atomic():
            if self.booking_slot is not None:
                self.booking_slot.save()

            return super().save(*args, **kwargs)

    def createCharge(self):
        charge = Charge(name=f"Charge for {self.name}", cost=self.cost, booking=self, customer=self.pet.customer)
        charge.save()

        return charge

    def _getNewBookingSlot(self):
        slot = BookingSlot.getSlot(self.start, self.end)

        if slot.service != self.service and slot.service is not None:
            raise BookingSlotIncorectService("Incorect Service")

        if slot.customer_count >= self.service.max_customer and self.pet.customer not in slot.customers:
            raise BookingSlotMaxCustomers("Max customers")

        if slot.pet_count >= self.service.max_pet:
            raise BookingSlotMaxPets("Max pets")

        if slot.overlaps():
            overlaps = slot.getOverlapping()

            if not all(all(b.id == self.id for b in o.bookings.all()) for o in overlaps):
                raise BookingSlotOverlaps("Overlaps another slot")

        return slot

    @property
    def canMove(self):
        return self.state in self.STATES_MOVEABLE

    def canComplete(self):
        return self.end < make_aware(datetime.now())

    def moveBooking(self, to):
        if not self.canMove:
            return

        delta = self.start - to
        self.start -= delta
        self.end -= delta

        self.booking_slot = self._getNewBookingSlot()

        return self.save()

    @transition(field=state, source=STATE_ENQUIRY, target=STATE_PRELIMINARY)
    def process(self):
        pass

    @transition(field=state, source=STATE_PRELIMINARY, target=STATE_CONFIRMED)
    def confirm(self):
        pass

    @transition(field=state, source=[STATE_ENQUIRY, STATE_PRELIMINARY, STATE_CONFIRMED], target=STATE_CANCELED)
    def cancel(self):
        self.booking_slot = None

    @transition(field=state, source=STATE_CANCELED, target=STATE_ENQUIRY)
    def reopen(self):
        pass

    @transition(field=state, source=STATE_CONFIRMED, target=STATE_COMPLETED, conditions=[canComplete])
    def complete(self):
        self.createCharge()

    @property
    def available_state_transitions(self) -> list[str]:
        return [i.name for i in self.get_available_state_transitions()]


@reversion.register()
class Service(models.Model):
    # Fields
    name = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    length = models.DurationField(blank=True, null=True)
    booked_length = models.DurationField(blank=True, null=True)
    cost = models.IntegerField(blank=True, null=True)
    cost_per_additional = models.IntegerField(blank=True, null=True)
    max_pet = models.IntegerField(blank=True, null=True)
    max_customer = models.IntegerField(blank=True, null=True)
    display_colour = models.CharField(max_length=255)  # ColorField(default="#000000")

    class Meta:
        ordering = ("-created",)

    def __str__(self):
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
        "cerberus.Customer",
        on_delete=models.CASCADE,
        related_name="addresss",
    )

    class Meta:
        ordering = ("-created",)

    def __str__(self):
        return f"{self.name}"
