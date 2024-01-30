# Standard Library

# Standard Library
from typing import TYPE_CHECKING

# Django
from django.db import models
from django.db.models.query import QuerySet
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

# Third Party
import reversion
from taggit.managers import TaggableManager

# Locals
from ..utils import choice_length

if TYPE_CHECKING:
    # Locals
    from .booking import Booking


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
