# Standard Library
from datetime import datetime
from typing import TYPE_CHECKING

# Django
from django.conf import settings
from django.db import models
from django.db.models import Count, F, Q, Sum
from django.db.models.functions import Concat
from django.db.models.query import QuerySet
from django.urls import reverse

# Third Party
import reversion
from djmoney.models.managers import money_manager
from moneyed import Money
from taggit.managers import TaggableManager

if TYPE_CHECKING:
    from . import Booking, Charge, Contact, Pet, Vet

# Locals
from .invoice import Invoice


class CustomerManager(models.Manager["Customer"]):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(
                invoiced_unpaid=Sum(F("invoices__adjustment"), default=0)
                + Sum(
                    (F("invoices__charges__line") * F("invoices__charges__quantity")),
                    filter=Q(invoices__state=Invoice.States.UNPAID.value),
                    default=0,
                ),
            )
            .annotate(
                unpaid_count=Count(
                    "invoices",
                    distinct=True,
                    filter=Q(invoices__state=Invoice.States.UNPAID.value),
                )
            )
            .annotate(
                overdue_count=Count(
                    "invoices",
                    distinct=True,
                    filter=Q(
                        invoices__state=Invoice.States.UNPAID.value,
                        invoices__due__lt=datetime.today(),
                    ),
                )
            )
            .order_by(*Customer._meta.ordering or list())
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

    name = models.GeneratedField(  # type: ignore
        expression=Concat("first_name", models.Value(" "), "last_name"),
        output_field=models.CharField(max_length=511),
        db_persist=True,
    )

    invoice_address = models.TextField(default="", blank=True)
    invoice_email = models.EmailField(default="", blank=True)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    active = models.BooleanField(default=True)

    vet: models.ForeignKey["Vet|None"] = models.ForeignKey(
        "cerberus.Vet",
        on_delete=models.SET_NULL,
        related_name="customers",
        blank=True,
        null=True,
    )

    tags = TaggableManager(blank=True)

    objects = money_manager(CustomerManager())

    _invoiced_unpaid = None

    class Meta:
        ordering = ("first_name", "last_name")

    def __str__(self) -> str:
        return f"{self.name}"

    def get_absolute_url(self) -> str:
        return reverse("customer_detail", kwargs={"pk": self.pk})

    @property
    def active_pets(self):
        return self.pets.filter(active=True)

    @property
    def invoiced_unpaid(self):
        return self._invoiced_unpaid

    @invoiced_unpaid.setter
    def invoiced_unpaid(self, value):
        self._invoiced_unpaid = Money(value, settings.DEFAULT_CURRENCY)

    def outstanding_invoices(self):
        return self.invoices.filter(state=Invoice.States.UNPAID.value).order_by("-due")

    @property
    def issues(self):
        issues = []

        if self.invoice_email == "":
            issues.append("no invoice email set")

        if "&" in self.last_name:
            issues.append("last name doesn't look right")

        return issues

    @property
    def bookings(self):
        bookings: list["Booking"] = []

        for pet in self.pets.all():
            bookings.extend(pet.bookings.all())

        return bookings
