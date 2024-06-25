# Standard Library
import datetime as dt
from calendar import MONDAY, Calendar, month_name
from collections import defaultdict, namedtuple
from collections.abc import Iterable

# Django
from django.contrib.humanize.templatetags import humanize
from django.db import transaction
from django.db.models import Count
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import RedirectView, TemplateView

# Third Party
from vanilla import FormView, ListView

# Locals
from ..filters import BookingFilter
from ..forms import BookingForm, CompletableBookingForm
from ..models import Booking
from ..utils import make_aware
from .crud_views import Actions, CRUDViews, Crumb
from .transition_view import TransitionView

BookingGroup = namedtuple("BookingDay", ["date", "bookings"])


class BookingList(ListView):
    def get_queryset(self):
        if self.model is not None:
            return self.model._default_manager.with_pets().with_customers().with_service()
        return super().get_queryset()


class BookingCRUD(CRUDViews):
    model = Booking
    form_class = BookingForm
    filter_class = BookingFilter
    sortable_fields = ["customer__name", "pets", "service", "start", "length"]
    lookup_field = "sqid"

    @classmethod
    def get_view_class(cls, action: Actions):
        if action == Actions.LIST:
            return BookingList
        return super().get_view_class(action)


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

        bookings = Booking.objects.active().filter(start__year=year).values("start__month").annotate(count=Count("id"))
        for stats in bookings:
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
        bookings = (
            Booking.objects.with_service().with_pets().active().filter(start__gte=start, end__lte=end).order_by("start")
        )

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
        bookings = (
            Booking.objects.with_service()
            .with_booking_slot()
            .with_pets()
            .active()
            .filter(start__gte=start, end__lte=end)
            .order_by("start")
        )

        bookings_by_date: dict[dt.time, list[Booking]] = defaultdict(list)
        for booking in bookings:
            bookings_by_date[booking.start.time()].append(booking)

        return bookings_by_date

    def organize_bookings(self, times: list[dt.datetime]) -> Iterable[BookingGroup]:
        bookings_by_date = self.grouped_bookings(times[0], times[-1])

        return [BookingGroup(t, bookings_by_date[t.time()]) for t in times]

    def get_times(self, date: dt.date, step: int = 15, start: int = 8, end: int = 17) -> list[dt.datetime]:
        min_time, max_time = Booking.get_min_max_time(date)

        bookings_start = getattr(min_time, "hour", start + 1) - 1
        bookings_end = getattr(max_time, "hour", end - 1) + 1

        start = min(start, bookings_start)
        end = max(end, bookings_end)
        steps = range(((end - start) * (60 // step)) + 1)
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
    lookup_field = "sqid"

    def htmx_render(self, request, action: str, **kwargs):
        lookup_value = kwargs.get(self.lookup_field)
        model = self.get_valid_model(lookup_value, action)
        return render(
            request,
            "cerberus/components/booking_row.html",
            {"booking": model, "hide_customer": True},
        )

    def get(self, request, action: str, **kwargs):
        redirect = super().get(request, action, **kwargs)
        if not request.htmx:
            return redirect

        return self.htmx_render(request, action, **kwargs)

    def post(self, request, action: str, **kwargs):
        redirect = super().post(request, action, **kwargs)
        if not request.htmx:
            return redirect

        return self.htmx_render(request, action, **kwargs)


class CompleteBookings(FormView):
    form_class = CompletableBookingForm
    template_name = "cerberus/booking_completable.html"

    def get_form(self, data=None, files=None, **kwargs):
        cls = self.get_form_class()
        timeframe = self.kwargs.get("timeframe", None)
        return cls(data=data, files=files, timeframe=timeframe, **kwargs)

    def form_valid(self, form):
        bookings = form.cleaned_data["bookings"]
        with transaction.atomic():
            for booking in bookings:
                booking.complete()

        clean_form = self.get_form()
        context = self.get_context_data(form=clean_form)
        context["success"] = True
        context["completed"] = len(bookings)

        return self.render_to_response(context)
