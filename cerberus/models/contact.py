# Standard Library
import re
from enum import Enum

# Django
from django.db import models
from django.utils.translation import gettext_lazy as _

# Third Party
import reversion

# Internals
from cerberus.exceptions import InvalidEmail


@reversion.register()
class Contact(models.Model):
    class Type(Enum):
        PHONE = _("phone")
        MOBILE = _("mobile")
        EMAIL = _("email")
        UNKNOWN = _("unknown")

    EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")
    MOBILE_REGEX = re.compile(r"^(\+447|\(?07)[0-9\(\)\s]+$")
    PHONE_REGEX = re.compile(r"^\+?[0-9\(\)\s]+$")

    # Fields
    name = models.CharField(max_length=255)
    details = models.CharField(max_length=255, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)

    # Relationship Fields
    customer = models.ForeignKey(
        "cerberus.Customer",
        on_delete=models.CASCADE,
        related_name="contacts",
    )

    @property
    def type(self) -> Type:
        details: str = self.details or ""

        if self.EMAIL_REGEX.match(details):
            return self.Type.EMAIL

        if self.MOBILE_REGEX.match(details):
            return self.Type.MOBILE

        if self.PHONE_REGEX.match(details):
            return self.Type.PHONE

        return self.Type.UNKNOWN

    class Meta:
        ordering = ("-created",)
        unique_together = ("name", "customer")

    def __str__(self) -> str:
        return f"{self.name}"

    def set_as_invoice(self):
        if self.type != self.Type.EMAIL:
            raise InvalidEmail("Can only set email as invoice email")

        self.customer.invoice_email = self.details
        return self.customer.save()
