# Django
from django.urls import path

# Internals
from cerberus import views

urlpatterns = (
    [
        path("", views.dashboard, name="dashboard"),
        path("bookings/<int:pk>/action/<str:action>", views.BookingStateActions.as_view(), name="booking_action"),
    ]
    + views.CustomerCRUD.get_urls()
    + views.PetCRUD.get_urls()
    + views.VetCRUD.get_urls()
    + views.InvoiceCRUD.get_urls()
    + views.BookingCRUD.get_urls()
)
