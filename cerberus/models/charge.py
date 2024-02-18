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

# Locals
from ..decorators import save_after
from ..exceptions import ChargeRefundError

if TYPE_CHECKING:
    # Locals
    from . import Customer, Invoice


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

    amount = MoneyField(max_digits=14)
    name = models.CharField(max_length=255)

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
            amount=-amount,
            parent_charge=self,
            customer=self.customer,
            invoice=None,
            state=self.States.REFUND.value,
        )

    def delete(self, using=None, keep_parents=False) -> None:
        return self.void()

    def save(self, *args, **kwargs):
        if self.invoice and not self.invoice.can_edit:
            allFields = {f.name for f in self._meta.concrete_fields if not f.primary_key}
            excluded = ("name", "amount", "customer")
            kwargs["update_fields"] = allFields.difference(excluded)

        if self.customer is None and self.invoice is not None:
            self.customer = self.invoice.customer

        return super().save(*args, **kwargs)


class QuantityChargeMixin(models.Model):
    quantity = models.IntegerField(default=1)
    amount: Money
    amount_currency: str

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        if "line" in kwargs:
            kwargs["amount"] = kwargs.pop("line") * kwargs.get("quantity", 1)

        super().__init__(*args, **kwargs)

    @property
    def line(self) -> Money:
        return Money(self.amount / self.quantity, self.amount_currency)

    @line.setter
    def line(self, value: Money | Decimal | int | float) -> None:
        self.amount = Money(value * self.quantity, self.amount_currency)


class QuantityCharge(QuantityChargeMixin, Charge):
    pass
