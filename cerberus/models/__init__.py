# Standard Library
from datetime import datetime, timedelta

# Internals
from cerberus.models.address import Address
from cerberus.models.booking import Booking, BookingCharge, BookingSlot
from cerberus.models.charge import Charge, QuantityCharge, QuantityChargeMixin
from cerberus.models.contact import Contact
from cerberus.models.customer import Customer
from cerberus.models.invoice import Invoice, InvoiceOpen, Payment
from cerberus.models.pet import Pet
from cerberus.models.service import Service
from cerberus.models.user_settings import UserSettings
from cerberus.models.vet import Vet


def get_default_due_date() -> datetime:
    return datetime.now() + timedelta(weeks=1)


__all__ = [
    "Address",
    "Booking",
    "BookingSlot",
    "BookingCharge",
    "Charge",
    "QuantityChargeMixin",
    "QuantityCharge",
    "Contact",
    "Customer",
    "Invoice",
    "InvoiceOpen",
    "Payment",
    "Pet",
    "Service",
    "UserSettings",
    "Vet",
    "get_default_due_date",
]
