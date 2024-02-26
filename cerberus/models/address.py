# Django
from django.db import models

# Third Party
import reversion


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
