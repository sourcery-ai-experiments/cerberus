# Standard Library
from datetime import datetime
from typing import TYPE_CHECKING

# Django
from django.db import models
from django.db.models.query import QuerySet
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

# Third Party
import reversion
from humanize import naturaldelta
from taggit.managers import TaggableManager

# Locals
from ..fields import SqidsModelField as SqidsField
from ..utils import choice_length

if TYPE_CHECKING:
    # Locals
    from . import Booking


class PetManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("customer")


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
    social_media_concent = models.CharField(
        default=Social.YES,
        choices=Social.choices,
        max_length=choice_length(Social),
    )
    sex = models.CharField(
        blank=True,
        default=Sex.__empty__,
        db_default=Sex.__empty__,
        choices=Sex.choices,
        max_length=choice_length(Sex),
    )  # type: ignore
    description = models.TextField(blank=True, default="")
    neutered = models.CharField(
        blank=True,
        default=Neutered.__empty__,
        db_default=Neutered.__empty__,
        choices=Neutered.choices,
        max_length=choice_length(Neutered),
    )  # type: ignore
    medical_conditions = models.TextField(blank=True, default="")
    treatment_limit = models.IntegerField(default=0)
    allergies = models.TextField(blank=True, default="")

    tags = TaggableManager(blank=True)

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

    sqid = SqidsField(real_field_name="id")

    objects = PetManager()

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return f"{self.name}"

    def get_absolute_url(self) -> str:
        return reverse("pet_detail", kwargs={"sqid": self.sqid})

    @property
    def name_with_owner(self) -> str:
        return f"{self.name} ({self.customer})"

    @property
    def age(self) -> str:
        if self.dob:
            return naturaldelta(datetime.now().date() - self.dob)
        return "Unknown"
