# Standard Library
import os
import re
from collections.abc import Callable, Iterable
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Optional

# Django
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.staticfiles import finders
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.db import models, transaction
from django.db.models import Count, F, Q, Sum, Value
from django.db.models.functions import Concat
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404, render  # noqa
from django.template import loader
from django.template.loader import get_template
from django.urls import reverse
from django.utils.timezone import make_aware
from django.utils.translation import gettext_lazy as _

# Third Party
import reversion
from django_fsm import FSMField, Transition, transition
from django_fsm_log.models import StateLog
from djmoney.models.fields import MoneyField
from djmoney.models.managers import money_manager
from model_utils.fields import MonitorField
from moneyed import Money
from polymorphic.models import PolymorphicModel
from taggit.managers import TaggableManager
from xhtml2pdf import pisa

# Locals
from .decorators import save_after
from .exceptions import (
    BookingSlotIncorectService,
    BookingSlotMaxCustomers,
    BookingSlotMaxPets,
    BookingSlotOverlaps,
    InvalidEmail,
)
from .utils import choice_length


class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    ui_settings = models.JSONField(default=dict)


class CustomerManager(models.Manager["Customer"]):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(name=Concat("first_name", Value(" "), "last_name"))
            .annotate(
                invoiced_unpaid=Sum(F("invoices__adjustment"), default=0)
                + Sum(
                    (F("invoices__charges__line") * F("invoices__charges__quantity")),
                    filter=Q(invoices__state=Invoice.States.UNPAID.value),
                    default=0,
                ),
            )
            .annotate(unpaid_count=Count("invoices", distinct=True, filter=Q(invoices__state=Invoice.States.UNPAID.value)))
            .annotate(
                overdue_count=Count(
                    "invoices",
                    distinct=True,
                    filter=Q(invoices__state=Invoice.States.UNPAID.value, invoices__due__lt=datetime.today()),
                )
            )
        )


@reversion.register()
class Customer(models.Model):
    id: int
    pets: "QuerySet[Pet]"
    contacts: "QuerySet[Contact]"
    charges: "QuerySet[Charge]"
    invoices: "QuerySet[Invoice]"
    unpaid_count: int
    overdue_count: int

    # Fields
    first_name = models.CharField(max_length=125)
    last_name = models.CharField(max_length=125)
    other_names = models.CharField(max_length=255, default="", blank=True)
    invoice_address = models.TextField(default="", blank=True)
    invoice_email = models.EmailField(default="", blank=True)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    active = models.BooleanField(default=True)

    vet = models.ForeignKey(
        "cerberus.Vet",
        on_delete=models.SET_NULL,
        related_name="customers",
        blank=True,
        null=True,
        default=None,
    )

    tags = TaggableManager(blank=True)

    objects = money_manager(CustomerManager())

    @property
    def active_pets(self):
        return self.pets.filter(active=True)

    class Meta:
        ordering = ("-created",)

    @property
    def name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @name.setter
    def name(self, value: str) -> None:
        # this is annotated for searching and sorting
        # but has a getter for nested serialization
        # so it needs a setter to stop attribution error
        pass

    _invoiced_unpaid = None

    @property
    def invoiced_unpaid(self):
        return self._invoiced_unpaid

    @invoiced_unpaid.setter
    def invoiced_unpaid(self, value):
        self._invoiced_unpaid = Money(value, "GBP")

    @property
    def issues(self):
        issues = []

        if self.invoice_email == "":
            issues.append("no invoice email set")

        if "&" in self.last_name:
            issues.append("last name doesn't look right")

        return issues

    def __str__(self) -> str:
        return f"{self.name}"

    @property
    def bookings(self):
        bookings: list["Booking"] = []

        for pet in self.pets.all():
            bookings.extend(pet.bookings.all())

        return bookings

    def get_absolute_url(self) -> str:
        return reverse("customer_detail", kwargs={"pk": self.pk})


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
        "cerberus.Customer",
        on_delete=models.PROTECT,
        related_name="pets",
    )
    vet = models.ForeignKey(
        "cerberus.Vet",
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

    def get_absolute_url(self) -> str:
        return reverse("pet_detail", kwargs={"pk": self.pk})


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

    def get_absolute_url(self) -> str:
        return reverse("vet_detail", kwargs={"pk": self.pk})


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
        "cerberus.Customer",
        on_delete=models.CASCADE,
        related_name="contacts",
    )

    @property
    def type(self) -> Type:
        details: str = self.details or ""

        if self.EMAIL_REGEX.match(details):
            return self.Type.EMAIL

        if self.MOBILE_REGEX.match(details):
            return self.Type.MOBILE

        if self.PHONE_REGEX.match(details):
            return self.Type.PHONE

        return self.Type.UNKNOWN

    class Meta:
        ordering = ("-created",)
        unique_together = ("name", "customer")

    def __str__(self) -> str:
        return f"{self.name}"

    def set_as_invoice(self):
        if self.type != self.Type.EMAIL:
            raise InvalidEmail("Can only set email as invoice email")

        self.customer.invoice_email = self.details
        return self.customer.save()


def get_default_due_date() -> datetime:
    return datetime.now() + timedelta(weeks=1)


@reversion.register()
class Charge(PolymorphicModel):
    class States(models.TextChoices):
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

    state = FSMField(default=States.UNPAID.value, choices=States.choices, protected=True)
    paid_on = MonitorField(monitor="state", when=[States.PAID.value], default=None, null=True)

    customer = models.ForeignKey(
        "cerberus.Customer",
        on_delete=models.SET_NULL,
        null=True,
        related_name="charges",
    )

    invoice = models.ForeignKey(
        "cerberus.Invoice",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="charges",
    )

    class Meta:
        ordering = ("created",)

    def __str__(self) -> str:
        return f"{self.name} - {self.total_money}"

    def __float__(self) -> float:
        return float(self.cost)

    def __add__(self, other) -> Money:
        return self.cost + other.cost if isinstance(other, Charge) else NotImplemented

    @property
    def total_money(self):
        return self.line * self.quantity

    @property
    def cost(self):
        return self.line.amount * self.quantity

    @cost.setter
    def set_cost(self, value):
        self.line = value / self.quantity

    @save_after
    @transition(field=state, source=States.UNPAID.value, target=States.PAID.value)
    def pay(self):
        pass

    @save_after
    @transition(field=state, source=States.UNPAID.value, target=States.VOID.value)
    def void(self) -> None:
        self.invoice = None

    @save_after
    @transition(field=state, source=States.PAID.value, target=States.REFUNDED.value)
    def refund(self) -> None:
        pass

    def delete(self) -> None:
        return self.void()

    def save(self, *args, **kwargs):
        if self.invoice and not self.invoice.can_edit:
            allFields = {f.name for f in self._meta.concrete_fields if not f.primary_key}
            excluded = ("name", "line", "quantity", "customer")
            kwargs["update_fields"] = allFields.difference(excluded)

        if self.customer is None and self.invoice is not None:
            self.customer = self.invoice.customer

        return super().save(*args, **kwargs)


# self.state == self.States.UNPAID.value and self.due is not None and self.due < date.today()
class InvoiceManager(models.Manager["Invoice"]):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(
                subtotal=Sum(F("charges__line") * F("charges__quantity")),
                total=F("adjustment") + F("subtotal"),
                overdue=Q(state=Invoice.States.UNPAID.value, due__lt=date.today()),
            )
        )


class Invoice(models.Model):
    charges: models.QuerySet["Charge"]
    payments: models.QuerySet["Payment"]
    get_available_state_transitions: Callable[[], Iterable[Transition]]

    class States(models.TextChoices):
        DRAFT = "draft"
        UNPAID = "unpaid"
        PAID = "paid"
        VOID = "void"

    details = models.TextField(blank=True, default="")
    due = models.DateField(blank=True, null=True, default=None)
    adjustment = MoneyField(default=0.0, max_digits=14, decimal_places=2, default_currency="GBP")

    customer_name = models.CharField(max_length=255, blank=True, null=True)
    sent_to = models.CharField(max_length=255, blank=True, null=True)
    invoice_address = models.TextField(default="", blank=True)

    state = FSMField(default=States.DRAFT.value, choices=States.choices, protected=True)
    paid_on = MonitorField(monitor="state", when=[States.PAID.value], default=None, null=True)
    sent_on = MonitorField(monitor="state", when=[States.UNPAID.value], default=None, null=True)

    send_notes = models.TextField(blank=True, default="", null=True)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)

    _can_edit = False

    customer = models.ForeignKey(
        "cerberus.Customer",
        on_delete=models.SET_NULL,
        null=True,
        related_name="invoices",
    )

    objects = money_manager(InvoiceManager())

    def __str__(self) -> str:
        return self.name

    def can_send(self) -> bool:
        return self.customer is not None and len(self.customer.issues) == 0

    @property
    def can_edit(self) -> bool:
        return self.state == self.States.DRAFT.value or self._can_edit

    @property
    def name(self) -> str:
        return f"INV-{self.pk:03}"

    @property
    def overdue(self) -> bool:
        return self.state == self.States.UNPAID.value and self.due is not None and self.due < date.today()

    @overdue.setter
    def overdue(self, value):
        pass

    @property
    def state_log(self):
        created = {
            "pk": 0,
            "timestamp": self.created,
            "source_state": None,
            "state": self.States.DRAFT,
            "transition": None,
            "description": "Created",
            "by": None,
        }
        createdLog = StateLog(**created)

        return [createdLog] + list(StateLog.objects.for_(self))

    @save_after
    @transition(
        field=state,
        source=States.DRAFT.value,
        target=States.UNPAID.value,
        conditions=[can_send],
    )
    def send(self, to=None, send_email=True, send_notes=None):
        self._can_edit = True
        self.customer_name = self.customer.name
        self.invoice_address = self.customer.invoice_address
        if self.due is None:
            self.due = date.today() + timedelta(weeks=1)

        self.send_notes = send_notes

        if send_email:
            self.sent_to = to or self.customer.invoice_email
            self.send_email([f"{self.customer.name} <{self.customer.invoice_email}>"])

    def send_email(self, to: list[str]):
        assert self.can_send(), "Unable to send email"

        html = loader.get_template("emails/invoice.html")
        txt = loader.get_template("emails/invoice.txt")

        context = {
            "invoice": self,
            "customer": self.customer,
            "send_notes": self.send_notes or "",
        }

        email = EmailMultiAlternatives(
            subject=f"Invoice {self.name} - Stretch there legs",
            body=txt.render(context),
            from_email="Stretch there legs - Accounts<admin@stretchtheirlegs.co.uk>",
            reply_to=["Stef <stef@stretchtheirlegs.co.uk>"],
            to=to,
        )

        results = self.get_pdf()
        if results.err:
            raise Exception(results.err)

        email.attach(f"{self.name}.pdf", results.dest.getvalue(), "application/pdf")
        email.attach_alternative(html.render(context), "text/html")

        return email.send()

    @property
    def paid(self):
        return sum(p.amount for p in self.payments.all())

    @property
    def unpaid(self):
        return (self.total or 0) - self.paid

    @save_after
    @transition(field=state, source=States.UNPAID.value, target=States.PAID.value)
    def pay(self):
        for charge in self.charges.all():
            charge.pay()

        payment = Payment(invoice=self, amount=self.unpaid)
        payment.save()

    @save_after
    @transition(field=state, source=(States.DRAFT.value, States.UNPAID.value), target=States.VOID.value)
    def void(self) -> None:
        pass

    def delete(self, force=False, *args, **kwargs) -> None:
        if self.state == self.States.DRAFT.value or force:
            super().delete(*args, **kwargs)
        else:
            self.void()

    @property
    def available_state_transitions(self) -> list[str]:
        return [i.name for i in self.get_available_state_transitions()]

    @property
    def issued(self):
        return self.sent_on or self.created

    def link_callback(self, uri, rel):
        """Convert HTML URIs to absolute system paths so xhtml2pdf can access
        those resources."""
        if result := finders.find(uri):
            if not isinstance(result, (list, tuple)):
                result = [result]
            result = [os.path.realpath(path) for path in result]
            path = result[0]
        else:
            sUrl = settings.STATIC_URL  # Typically /static/
            sRoot = settings.STATIC_ROOT  # Typically /home/userX/project_static/
            mUrl = settings.MEDIA_URL  # Typically /media/
            mRoot = settings.MEDIA_ROOT  # Typically /home/userX/project_static/media/

            if uri.startswith(mUrl):
                path = os.path.join(mRoot, uri.replace(mUrl, ""))
            elif uri.startswith(sUrl):
                path = os.path.join(sRoot, uri.replace(sUrl, ""))
            else:
                return uri

        # make sure that file exists
        if not os.path.isfile(path):
            raise Exception(f"media URI must start with {sUrl} or {mUrl}")
        return path

    @property
    def subtotal(self) -> Money:
        return Money(0, "GBP") + sum(c.total_money for c in self.charges.all())

    @subtotal.setter
    def subtotal(self, value):
        pass

    @property
    def total(self) -> Money:
        return self.subtotal + self.adjustment

    @total.setter
    def total(self, value):
        pass

    def get_pdf(self, renderTo=None):
        template_path = "cerberus/invoice.html"
        context = {
            "invoice": self,
        }

        template = get_template(template_path)
        html = template.render(context)

        return pisa.CreatePDF(html, dest=renderTo, link_callback=self.link_callback)

    def add_open(self):
        o = InvoiceOpen(invoice=self)
        return o.save()

    def save(self, *args, **kwargs) -> None:
        if not self.can_edit:
            allFields = {f.name for f in self._meta.concrete_fields if not f.primary_key}
            excluded = (
                "invoice",
                "details",
                "sent_to",
                "adjustment",
                "adjustment_currency",
                "customer_name",
                "due",
                "adjustment",
            )
            kwargs["update_fields"] = allFields.difference(excluded)
        self._can_edit = False

        super().save(*args, **kwargs)


class InvoiceOpen(models.Model):
    opened = models.DateTimeField(auto_now_add=True, editable=False)
    invoice = models.ForeignKey("cerberus.Invoice", on_delete=models.CASCADE, related_name="opens")


class Payment(models.Model):
    amount = MoneyField(default=0.0, max_digits=14, decimal_places=2, default_currency="GBP")
    invoice = models.ForeignKey(
        "cerberus.Invoice",
        on_delete=models.PROTECT,
        null=True,
        related_name="payments",
        limit_choices_to={"state": Invoice.States.UNPAID.value},
    )

    customer = models.ForeignKey(
        "cerberus.Customer",
        on_delete=models.PROTECT,
        related_name="payments",
    )

    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        constraints = [
            models.CheckConstraint(name="%(app_label)s_%(class)s_gte_0", check=models.Q(amount__gte=0)),
        ]

    def __str__(self) -> str:
        return f"{self.amount} for {self.invoice}"

    def save(self, *args, **kwargs) -> None:
        if not hasattr(self, "customer") and self.invoice is not None:
            self.customer = self.invoice.customer
        return super().save(*args, **kwargs)


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
    class States(models.TextChoices):
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
    name = models.CharField(max_length=520)
    cost = models.PositiveIntegerField()
    start = models.DateTimeField()
    end = models.DateTimeField()

    state = FSMField(default=States.PRELIMINARY.value, choices=States.choices, protected=True)

    # Relationship Fields
    pet = models.ForeignKey("cerberus.Pet", on_delete=models.PROTECT, related_name="bookings")
    service = models.ForeignKey("cerberus.Service", on_delete=models.PROTECT, related_name="bookings")
    booking_slot = models.ForeignKey("cerberus.BookingSlot", on_delete=models.PROTECT, related_name="bookings")

    charges = GenericRelation(Charge)

    class Meta:
        ordering = ("-created",)

    def __str__(self) -> str:
        return f"{self.start} - {self.end}"

    def save(self, *args, **kwargs) -> None:
        self.name = f"{self.pet.name} {self.service.name}"

        with transaction.atomic():
            if self.pk is None:
                self.booking_slot = self._get_new_booking_slot()

            if self.booking_slot is not None:
                self.booking_slot.save()

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
        ordering = ("name",)

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
        "cerberus.Customer",
        on_delete=models.CASCADE,
        related_name="addresses",
    )

    class Meta:
        ordering = ("-created",)

    def __str__(self) -> str:
        return f"{self.name}"
