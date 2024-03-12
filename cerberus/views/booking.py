# Standard Library
import datetime
from calendar import MONDAY, Calendar
from collections import defaultdict, namedtuple
from collections.abc import Iterable

# Django
from django.http import Http404
from django.views.generic import RedirectView, TemplateView

# Third Party
from dateutil.relativedelta import relativedelta

# Locals
from ..forms import BookingForm
from ..models import Booking
from .crud_views import CRUDViews
from .transition_view import TransitionView

BookingDay = namedtuple("BookingDay", ["date", "bookings"])


class BookingCRUD(CRUDViews):
    model = Booking
    form_class = BookingForm
    sortable_fields = ["pet__customer", "pet", "service", "start", "length"]


class BookingCalenderRedirect(RedirectView):
    pattern_name = "booking_calender_month"

    def get_redirect_url(self, *args, **kwargs):
        kwargs["year"] = datetime.datetime.now().year
        kwargs["month"] = datetime.datetime.now().month

        return super().get_redirect_url(*args, **kwargs)


class BookingCalenderMonth(TemplateView):
    template_name = "cerberus/booking_calender_month.html"

    def grouped_bookings(self, start: datetime.date, end: datetime.date) -> dict[datetime.date, list[Booking]]:
        bookings = Booking.objects.filter(start__gte=start, end__lte=end).order_by("start")

        bookings_by_date: dict[datetime.date, list[Booking]] = defaultdict(list)
        for booking in bookings:
            bookings_by_date[booking.start.date()].append(booking)

        return bookings_by_date

    def organize_bookings(self, dates: list[datetime.date]) -> Iterable[BookingDay]:
        bookings_by_date = self.grouped_bookings(dates[0], dates[-1])

        return [BookingDay(date, bookings_by_date[date]) for date in dates]

    def get_context_data(self, year, month, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            date = datetime.datetime(year=year, month=month, day=1)
        except ValueError as e:
            raise Http404(f"month {month} not found") from e

        calendar = Calendar(MONDAY)

        context["date"] = date
        context["year"] = year
        context["month"] = month
        context["next_month"] = date + relativedelta(months=1)
        context["prev_month"] = date + relativedelta(months=-1)
        context["calendar"] = self.organize_bookings(list(calendar.itermonthdates(year, month)))
        context["today"] = datetime.date.today()
        context["days"] = calendar.iterweekdays()

        return context


class BookingCalenderDay(TemplateView):
    template_name = "cerberus/booking_calender_day.html"

    def get_context_data(self, year, month, day, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            date = datetime.datetime(year=year, month=month, day=1)
        except ValueError as e:
            raise Http404("date not found") from e

        context["date"] = date
        context["year"] = year
        context["month"] = month
        context["day"] = day

        return context


class BookingStateActions(TransitionView):
    model = Booking
    field = "state"
