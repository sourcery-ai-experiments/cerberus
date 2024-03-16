# Django
from django.urls import path

# Locals
from .. import views

urlpatterns = (
    [
        path("", views.dashboard, name="dashboard"),
        path("booking/<int:pk>/action/<str:action>/", views.BookingStateActions.as_view(), name="booking_action"),
        path("booking/calender/", views.BookingCalenderRedirect.as_view(), name="booking_calender_current"),
        path(
            "booking/calender/<int:year>/",
            views.BookingCalenderYear.as_view(),
            name="booking_calender_year",
        ),
        path(
            "booking/calender/<int:year>/<int:month>/",
            views.BookingCalenderMonth.as_view(),
            name="booking_calender_month",
        ),
        path(
            "booking/calender/<int:year>/<int:month>/<int:day>",
            views.BookingCalenderDay.as_view(),
            name="booking_calender_day",
        ),
    ]
    + views.CustomerCRUD.get_urls()
    + views.PetCRUD.get_urls()
    + views.VetCRUD.get_urls()
    + views.InvoiceCRUD.get_urls()
    + views.BookingCRUD.get_urls()
    + views.ServiceCRUD.get_urls()
)
