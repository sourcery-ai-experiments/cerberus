# Standard Library
from datetime import datetime
from typing import TYPE_CHECKING, Self

# Django
from django.conf import settings
from django.db import models
from django.db.models import Count, F, Prefetch, Q, Sum
from django.db.models.functions import Concat
from django.db.models.query import QuerySet
from django.urls import reverse

# Third Party
import reversion
from djmoney.models.managers import money_manager
from moneyed import Money
from taggit.managers import TaggableManager

# Locals
from ..fields import SqidsModelField as SqidsField

if TYPE_CHECKING:
    from . import Booking, Charge, Contact, Vet

# Locals
from .booking import Booking, BookingStates
from .invoice import Invoice
from .pet import Pet


class CustomerQuerySet(models.QuerySet["Customer"]):
    def with_pets(self) -> Self:
        active_pets_prefetch = Prefetch("pets", queryset=Pet.objects.filter(active=True), to_attr="active_pets")

        return self.prefetch_related("pets", active_pets_prefetch)

    def with_totals(self) -> Self:
        return self.annotate(
            invoiced_unpaid=Sum(F("invoices__adjustment"), default=0)
            + Sum(
                (F("invoices__charges__line") * F("invoices__charges__quantity")),
                filter=Q(invoices__state=Invoice.States.UNPAID.value),
                default=0,
            ),
        )

    def with_counts(self) -> Self:
        return (
            self.annotate(
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
            .annotate(
                uninvoiced_count=Count(
                    "charges",
                    distinct=True,
                    filter=Q(charges__invoice=None),
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

    sqid = SqidsField(real_field_name="id")

    tags = TaggableManager(blank=True)

    objects = money_manager(CustomerQuerySet.as_manager())

    _invoiced_unpaid = None

    class Meta:
        ordering = ("first_name", "last_name")

    def __str__(self) -> str:
        return f"{self.name}"

    def get_absolute_url(self) -> str:
        return reverse("customer_detail", kwargs={"sqid": self.sqid})

    @property
    def invoiced_unpaid(self):
        return self._invoiced_unpaid or Money(
            (
                self.invoices.filter(state=Invoice.States.UNPAID.value).aggregate(
                    invoiced_unpaid=Sum(F("adjustment") + F("charges__line") * F("charges__quantity"))
                )["invoiced_unpaid"]
                or 0
            ),
            settings.DEFAULT_CURRENCY,
        )

    @invoiced_unpaid.setter
    def invoiced_unpaid(self, value):
        self._invoiced_unpaid = Money(value, settings.DEFAULT_CURRENCY)

    @property
    def issues(self):
        issues = []

        if self.invoice_email == "":
            issues.append("no invoice email set")

        if "&" in self.last_name:
            issues.append("last name doesn't look right")

        return issues

    @property
    def bookings(self) -> QuerySet["Booking"]:
        return Booking.objects.filter(pet__in=self.pets.all()).order_by("start")

    @property
    def upcoming_bookings(self) -> QuerySet["Booking"]:
        return self.bookings.filter(start__gte=datetime.today()).exclude(
            state__in=[BookingStates.CANCELED.value, BookingStates.COMPLETED.value]
        )
