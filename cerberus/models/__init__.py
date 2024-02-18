# Standard Library
from datetime import datetime, timedelta

# Locals
from .address import Address
from .booking import Booking, BookingCharge, BookingSlot
from .charge import Charge, QuantityCharge, QuantityChargeMixin
from .contact import Contact
from .customer import Customer
from .invoice import Invoice, InvoiceOpen, Payment
from .pet import Pet
from .service import Service
from .user_settings import UserSettings
from .vet import Vet


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
