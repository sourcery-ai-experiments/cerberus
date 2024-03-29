# Standard Library
import datetime as dt
from calendar import MONDAY, Calendar, month_name
from collections import defaultdict, namedtuple
from collections.abc import Iterable

# Django
from django.contrib.humanize.templatetags import humanize
from django.db.models import Count
from django.http import Http404
from django.urls import reverse_lazy
from django.views.generic import RedirectView, TemplateView

# Locals
from ..forms import BookingForm
from ..models import Booking
from ..utils import make_aware
from .crud_views import CRUDViews, Crumb
from .transition_view import TransitionView

BookingGroup = namedtuple("BookingDay", ["date", "bookings"])


class BookingCRUD(CRUDViews):
    model = Booking
    form_class = BookingForm
    sortable_fields = ["customer__name", "pets", "service", "start", "length"]


class BookingCalenderRedirect(RedirectView):
    pattern_name = "booking_calender_month"

    def get_redirect_url(self, *args, **kwargs):
        kwargs["year"] = dt.datetime.now().year
        kwargs["month"] = dt.datetime.now().month

        return super().get_redirect_url(*args, **kwargs)


class CalendarBreadCrumbs:
    def get_breadcrumbs(self, year: int, month: int | None = None, day: int | None = None) -> list[Crumb]:
        month_url = reverse_lazy("booking_calender_month", kwargs={"year": year, "month": month})
        day_url = reverse_lazy("booking_calender_day", kwargs={"year": year, "month": month, "day": day})

        crumbs = [
            Crumb("Dashboard", reverse_lazy("dashboard")),
            Crumb("Bookings", reverse_lazy("booking_list")),
            Crumb(year, reverse_lazy("booking_calender_year", kwargs={"year": year})),
            Crumb(month_name[month], month_url) if month is not None else None,
            Crumb(humanize.ordinal(day), day_url) if day is not None else None,
        ]

        return list(filter(lambda crumb: crumb is not None, crumbs))


BookingMonth = namedtuple("BookingMonth", ["name", "i", "booking_count"])


class BookingCalenderYear(TemplateView, CalendarBreadCrumbs):
    template_name = "cerberus/booking_calender_year.html"

    def get_booking_stats(self, year) -> dict[int, int]:
        month_stats: dict[int, int] = defaultdict(int)

        for stats in Booking.active.filter(start__year=year).values("start__month").annotate(count=Count("id")):
            month_stats[stats["start__month"]] = stats["count"]

        return month_stats

    def get_months(self, year) -> Iterable[BookingMonth]:
        stats = self.get_booking_stats(year)

        for i in range(1, 13):
            yield BookingMonth(month_name[i], i, stats[i])

    def get_context_data(self, year, **kwargs):
        context = super().get_context_data(year=year, **kwargs)

        try:
            date = dt.datetime(year=year, month=1, day=1)
        except ValueError as e:
            raise Http404(f"year {year} not found") from e

        context["date"] = date
        context["prev_year"] = year - 1
        context["year"] = year
        context["next_year"] = year + 1
        context["today"] = date.today()
        context["months"] = self.get_months(year)
        context["breadcrumbs"] = self.get_breadcrumbs(year)

        return context


class BookingCalenderMonth(TemplateView, CalendarBreadCrumbs):
    template_name = "cerberus/booking_calender_month.html"

    def grouped_bookings(self, start: dt.date, end: dt.date) -> dict[dt.date, list[Booking]]:
        bookings = Booking.active.filter(start__gte=start, end__lte=end).order_by("start")

        bookings_by_date: dict[dt.date, list[Booking]] = defaultdict(list)
        for booking in bookings:
            bookings_by_date[booking.start.date()].append(booking)

        return bookings_by_date

    def organize_bookings(self, dates: list[dt.date]) -> Iterable[BookingGroup]:
        bookings_by_date = self.grouped_bookings(dates[0], dates[-1])

        return [BookingGroup(date, bookings_by_date[date]) for date in dates]

    def get_context_data(self, year=None, month=None, **kwargs):
        now = dt.datetime.now()
        year = year or now.year
        month = month or now.month
        context = super().get_context_data(year=year, month=month, **kwargs)

        try:
            date = dt.datetime(year=year, month=month, day=1)
        except ValueError as e:
            raise Http404(f"month {month} not found") from e

        calendar = Calendar(MONDAY)

        context["date"] = date
        context["year"] = year
        context["month"] = month
        context["next_month"] = (date + dt.timedelta(days=32)).replace(day=1)
        context["prev_month"] = (date + dt.timedelta(days=-1)).replace(day=1)
        context["calendar"] = self.organize_bookings(list(calendar.itermonthdates(year, month)))
        context["today"] = date.today()
        context["days"] = calendar.iterweekdays()
        context["breadcrumbs"] = self.get_breadcrumbs(year, month)

        return context


class BookingCalenderDay(TemplateView, CalendarBreadCrumbs):
    template_name = "cerberus/booking_calender_day.html"

    def grouped_bookings(self, start: dt.datetime, end: dt.datetime) -> dict[dt.time, list[Booking]]:
        bookings = Booking.active.filter(start__gte=start, end__lte=end).order_by("start")

        bookings_by_date: dict[dt.time, list[Booking]] = defaultdict(list)
        for booking in bookings:
            bookings_by_date[booking.start.time()].append(booking)

        return bookings_by_date

    def organize_bookings(self, times: list[dt.datetime]) -> Iterable[BookingGroup]:
        bookings_by_date = self.grouped_bookings(times[0], times[-1])

        return [BookingGroup(t, bookings_by_date[t.time()]) for t in times]

    def get_times(self, date: dt.date, step: int = 15, start: int = 8, end: int = 17) -> list[dt.datetime]:
        min_time, max_time = Booking.get_mix_max_time(date)

        bookings_start = getattr(min_time, "hour", start + 1) - 1
        bookings_end = getattr(max_time, "hour", end - 1) + 1

        start = min(start, bookings_start)
        end = max(end, bookings_end)
        steps = range(0, ((end - start) * (60 // step)) + 1)
        return [make_aware(date + dt.timedelta(hours=start, minutes=15 * i)) for i in steps]

    def get_context_data(self, year=None, month=None, day=None, **kwargs):
        now = dt.datetime.now()
        year = year or now.year
        month = month or now.month
        day = day or now.day
        context = super().get_context_data(year=year, month=month, day=day, **kwargs)

        try:
            date = dt.datetime(year=year, month=month, day=day)
        except ValueError as e:
            raise Http404("date not found") from e

        times = self.get_times(date)

        context["date"] = date
        context["year"] = year
        context["month"] = month
        context["day"] = day
        context["next_day"] = date + dt.timedelta(days=1)
        context["prev_day"] = date + dt.timedelta(days=-1)
        context["booking_times"] = self.organize_bookings(times)
        context["breadcrumbs"] = self.get_breadcrumbs(year, month, day)

        return context


class BookingStateActions(TransitionView):
    model = Booking
    field = "state"
