# Standard Library

# Django
# Django
from django.db import models
from django.urls import reverse

# Third Party
import reversion


@reversion.register()
class Vet(models.Model):
    # Fields
    name = models.CharField(max_length=255)
    phone = models.CharField(blank=True, default="", max_length=128)
    details = models.TextField(blank=True, default="")
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return f"{self.name}"

    def get_absolute_url(self) -> str:
        return reverse("vet_detail", kwargs={"pk": self.pk})
