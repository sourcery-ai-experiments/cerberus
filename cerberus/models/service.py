# Standard Library
from datetime import timedelta

# Django
from django.db import models
from django.urls import reverse

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
    cost = MoneyField(max_digits=14)
    cost_per_additional = MoneyField(max_digits=14, default=None, blank=True, null=True)
    max_pet = models.IntegerField(default=1)
    max_customer = models.IntegerField(default=1)
    display_colour = models.CharField(max_length=255)  # ColorField(default="#000000")

    class Meta:
        ordering = ("name",)
        unique_together = (("name", "cost", "max_pet", "max_customer", "length"),)

    def __str__(self) -> str:
        return f"{self.name}"

    def get_absolute_url(self) -> str:
        return reverse("service_detail", kwargs={"pk": self.pk})

    def length_seconds(self) -> int:
        return int(self.length.total_seconds())

    def length_minutes(self) -> int:
        return self.length_seconds() // 60
