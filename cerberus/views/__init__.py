# Locals
from .booking import (
    BookingCalenderDay,
    BookingCalenderMonth,
    BookingCalenderRedirect,
    BookingCalenderYear,
    BookingCRUD,
    BookingStateActions,
)
from .invoice import InvoiceCreateView, InvoiceCRUD, InvoiceUpdateView
from .views import CustomerCRUD, PetCRUD, ServiceCRUD, VetCRUD, dashboard

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
]
