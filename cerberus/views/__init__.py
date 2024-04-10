# Locals
from .booking import (
    BookingCalenderDay,
    BookingCalenderMonth,
    BookingCalenderRedirect,
    BookingCalenderYear,
    BookingCRUD,
    BookingStateActions,
)
from .customer import ContactCreateView, CustomerCRUD
from .invoice import InvoiceActionsView, InvoiceCreateView, InvoiceCRUD, InvoiceUpdateView
from .views import PetCRUD, ServiceCRUD, VetCRUD, dashboard

__all__ = [
    "dashboard",
    "CustomerCRUD",
    "PetCRUD",
    "VetCRUD",
    "ServiceCRUD",
    "BookingCRUD",
    "BookingStateActions",
    "BookingCalenderYear",
    "BookingCalenderMonth",
    "BookingCalenderDay",
    "BookingCalenderRedirect",
    "InvoiceUpdateView",
    "InvoiceCreateView",
    "InvoiceCRUD",
    "InvoiceActionsView",
    "ContactCreateView",
]
