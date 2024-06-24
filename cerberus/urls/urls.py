# Django
from django.urls import path, register_converter

# Locals
from .. import views


class PaddedIntConverter:
    regex = "[0-9]+"

    def to_python(self, value):
        return int(value)

    def to_url(self, value):
        return f"{value:05d}"


register_converter(PaddedIntConverter, "pint")


urlpatterns = (
    [
        path(
            "",
            views.dashboard,
            name="dashboard",
        ),
        path(
            "booking/<str:sqid>/action/<str:action>/",
            views.BookingStateActions.as_view(),
            name="booking_action",
        ),
        path(
            "booking/calender/<int:year>/",
            views.BookingCalenderYear.as_view(),
            name="booking_calender_year",
        ),
        path(
            "booking/calender/",
            views.BookingCalenderMonth.as_view(),
            name="booking_calender_month",
        ),
        path(
            "booking/calender/<int:year>/<int:month>/",
            views.BookingCalenderMonth.as_view(),
            name="booking_calender_month",
        ),
        path(
            "booking/calender/today",
            views.BookingCalenderDay.as_view(),
            name="booking_calender_day",
        ),
        path(
            "booking/calender/<int:year>/<int:month>/<int:day>",
            views.BookingCalenderDay.as_view(),
            name="booking_calender_day",
        ),
        path(
            "booking/completable",
            views.CompleteBookings.as_view(),
            name="booking_completable",
        ),
        path(
            "invoice/<int:pk>/action/<str:action>/",
            views.InvoiceActionsView.as_view(),
            name="invoice_action",
        ),
        path(
            "customer/<int:pk>/contact/create",
            views.ContactCreateView.as_view(),
            name="contact_create",
        ),
    ]
    + views.CustomerCRUD.get_urls()
    + views.PetCRUD.get_urls()
    + views.VetCRUD.get_urls()
    + views.InvoiceCRUD.get_urls()
    + views.BookingCRUD.get_urls()
    + views.ServiceCRUD.get_urls()
)
