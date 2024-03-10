# Locals
from .booking import BookingCRUD, BookingStateActions
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
    "InvoiceUpdateView",
    "InvoiceCreateView",
    "InvoiceCRUD",
]
