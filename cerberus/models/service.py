# Standard Library
from datetime import timedelta

# Django
from django.db import models

# Third Party
import reversion
from djmoney.models.fields import MoneyField


@reversion.register()
class Service(models.Model):
    # Fields
    name = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    length = models.DurationField(default=timedelta(minutes=60))
    booked_length = models.DurationField(default=timedelta(minutes=120))
    cost = MoneyField(max_digits=14, decimal_places=2, default_currency="GBP")  # type: ignore
    cost_per_additional = MoneyField(max_digits=14, decimal_places=2, default_currency="GBP", default=0)  # type: ignore
    max_pet = models.IntegerField(default=1)
    max_customer = models.IntegerField(default=1)
    display_colour = models.CharField(max_length=255)  # ColorField(default="#000000")

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return f"{self.name}"
