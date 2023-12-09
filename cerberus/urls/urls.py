# Django
from django.urls import path

# Locals
from .. import views

# from ..views import dashboard, ListCustomer


urlpatterns = (
    [
        path("", views.dashboard, name="dashboard"),
        path("invoice/download/INV-<int:pk>.pdf", views.pdf, name="invoice_pdf"),
        path("bookings/<int:pk>/action/<str:action>", views.BookingStateActions.as_view(), name="booking_action"),
    ]
    + views.CustomerCRUD.get_urls()
    + views.PetCRUD.get_urls()
    + views.VetCRUD.get_urls()
    + views.InvoiceCRUD.get_urls()
    + views.BookingCRUD.get_urls()
)
