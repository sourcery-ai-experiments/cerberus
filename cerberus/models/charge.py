# Standard Library
from collections.abc import Callable, Iterable

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
