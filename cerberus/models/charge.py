# Standard Library
from collections.abc import Callable, Iterable
from decimal import Decimal
from typing import TYPE_CHECKING, Self

# Django
from django.db import models

# Third Party
import reversion
from django_fsm import FSMField, Transition, transition
from djmoney.models.fields import MoneyField
from model_utils.fields import MonitorField
from moneyed import Money
from polymorphic.models import PolymorphicModel
from polymorphic.query import PolymorphicQuerySet

# Locals
from ..decorators import save_after
from ..exceptions import ChargeRefundError

if TYPE_CHECKING:
    # Locals
    from . import Customer, Invoice


class ChargeQuerySet(PolymorphicQuerySet):
    def uninvoiced(self):
        return self.filter(invoice__isnull=True)

    def refundable(self):
        return self.filter(state=Charge.States.PAID.value)

    def refunded(self):
        return self.filter(state=Charge.States.REFUND.value)

    def voided(self):
        return self.filter(state=Charge.States.VOID.value)


@reversion.register()
class Charge(PolymorphicModel):
    class States(models.TextChoices):
        UNPAID = "unpaid"
        PAID = "paid"
        VOID = "void"
        REFUND = "refund"

    id: int
    get_all_state_transitions: Callable[[], Iterable[Transition]]
    get_available_state_transitions: Callable[[], Iterable[Transition]]

    # Fields
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)

    name = models.CharField(max_length=255)
    line = MoneyField(max_digits=14)
    quantity = models.IntegerField(default=1)

    state = FSMField(default=States.UNPAID.value, choices=States.choices, protected=True)  # type: ignore
    paid_on = MonitorField(monitor="state", when=[States.PAID.value], default=None, null=True)  # type: ignore

    parent_charge: models.ForeignKey["Charge|None"] = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        default=None,
        related_name="child_charges",
    )

    customer: models.ForeignKey["Customer|None"] = models.ForeignKey(
        "cerberus.Customer",
        on_delete=models.SET_NULL,
        null=True,
        related_name="charges",
    )

    invoice: models.ForeignKey["Invoice|None"] = models.ForeignKey(
        "cerberus.Invoice",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="charges",
    )

    objects = ChargeQuerySet.as_manager()

    class Meta:
        ordering = ("created",)

    def __str__(self) -> str:
        return f"{self.name} - {self.amount}"

    def __float__(self) -> float:
        return float(self.cost)

    def __add__(self, other) -> Money:
        return self.cost + other.cost if isinstance(other, Charge) else NotImplemented

    @save_after
    @transition(field=state, source=States.UNPAID.value, target=States.PAID.value)
    def pay(self):
        pass

    @save_after
    @transition(field=state, source=States.UNPAID.value, target=States.VOID.value)
    def void(self) -> None:
        self.invoice = None

    def get_refunds(self) -> Iterable[Self]:
        return self.__class__.objects.filter(parent_charge=self, state=self.States.REFUND.value)

    def refund(self, amount: Money | Decimal | int | float | None = None) -> Self:
        refunded = sum((refund.amount for refund in self.get_refunds()), Money(0, self.amount_currency))

        if refunded >= self.amount:
            raise ChargeRefundError("Charge has already been refunded in full")

        refundable = self.amount - (-refunded)
        amount = amount or refundable
        if not isinstance(amount, Money):
            amount = Money(amount, self.amount_currency)

        if amount > refundable:
            raise ChargeRefundError("Refund amount exceeds the refundable amount")

        return self.__class__.objects.create(
            name=f"{self.name} - Refund",
            line=-amount,
            parent_charge=self,
            customer=self.customer,
            invoice=None,
            state=self.States.REFUND.value,
        )

    def delete(self, using=None, keep_parents=False) -> None:
        return self.void()

    @property
    def amount(self) -> Money:
        return self.line * self.quantity  # type: ignore

    @property
    def amount_currency(self) -> str:
        return self.line_currency

    def save(self, *args, **kwargs):
        if self.invoice and not self.invoice.can_edit:
            all_fields = {f.name for f in self._meta.concrete_fields if not f.primary_key}
            excluded = ("name", "line", "quantity", "customer")
            kwargs["update_fields"] = all_fields.difference(excluded)

        if self.customer is None and self.invoice is not None:
            self.customer = self.invoice.customer

        return super().save(*args, **kwargs)
