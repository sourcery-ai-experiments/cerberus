# Standard Library
from datetime import datetime
from enum import Enum

# Django
from django import forms

# Third Party
from django_filters import rest_framework as filters
from django_filters.widgets import RangeWidget

# Locals
from .models import Booking, Customer, Invoice, Pet, Service, Vet
from .models.booking import BookingStates

ACTIVE_CHOICES = ((True, "Active"), (False, "Inactive"))


def strtobool(value: str) -> bool:
    return value.lower() in {"yes", "true", "y", "t", "1"}


class Switch(forms.widgets.Input):
    template_name = "forms/widgets/switch.html"
    input_type = "checkbox"


class RangeInput(RangeWidget):
    template_name = "forms/widgets/range_input.html"


class DateRangeInput(RangeWidget):
    template_name = "forms/widgets/date_range_input.html"


class CheckboxSelectMultipleDropdown(forms.CheckboxSelectMultiple):
    template_name = "forms/widgets/checkbox_select_multiple_dropdown.html"
    option_template_name = "forms/widgets/checkbox_select_multiple_dropdown.html"


class FilterDefaults(filters.FilterSet):
    default_filters = {}

    def __init__(self, data=None, *args, **kwargs):
        if data is not None:
            data = data.copy()
            for key, value in self.default_filters.items():
                if key not in data:
                    data[key] = value

        super().__init__(data, *args, **kwargs)


class PetFilter(FilterDefaults):
    active = filters.TypedChoiceFilter(choices=ACTIVE_CHOICES, coerce=strtobool, widget=Switch)
    name = filters.CharFilter(lookup_expr="icontains", label="Name")
    customer__name = filters.CharFilter(lookup_expr="icontains", label="Customer")

    default_filters = {
        "active": True,
    }

    class Meta:
        model = Pet
        fields = ["active"]


class CustomerFilter(FilterDefaults):
    class Statuses(Enum):
        BOOKINGS = "Bookings"
        UNINVOICED = "Uninvoiced"
        UNPAID = "Unpaid"
        OVERDUE = "Overdue"

        @classmethod
        def pairs(cls, filter: list = []) -> list[tuple[str, str]]:
            return [(status.name, status.value) for status in cls if status not in filter]

    status = filters.ChoiceFilter(choices=Statuses.pairs([Statuses.BOOKINGS]), method="filter_status", label="Status")
    active = filters.TypedChoiceFilter(choices=ACTIVE_CHOICES, coerce=strtobool, widget=Switch)
    name = filters.CharFilter(lookup_expr="icontains", label="Name")
    pets__name = filters.CharFilter(lookup_expr="icontains", label="Pet")

    default_filters = {
        "active": True,
    }

    class Meta:
        model = Customer
        fields = ["active"]

    def filter_status(self, queryset, name, value):
        match value:
            case self.Statuses.BOOKINGS.name:
                return queryset.filter(bookings__isnull=False, bookings__end__gte=datetime.now())
            case self.Statuses.UNINVOICED.name:
                return queryset.filter(charges__isnull=False, charges__invoice=None)
            case self.Statuses.UNPAID.name:
                return queryset.filter(invoices__state=Invoice.States.UNPAID)
            case self.Statuses.OVERDUE.name:
                return queryset.filter(invoices__state=Invoice.States.UNPAID, invoices__due__lt=datetime.now())
            case _:
                return queryset


class BookingFilter(FilterDefaults):
    state = filters.MultipleChoiceFilter(choices=BookingStates.choices, widget=CheckboxSelectMultipleDropdown)
    date = filters.DateFromToRangeFilter(widget=DateRangeInput, field_name="start", lookup_expr="date")
    service__name = filters.MultipleChoiceFilter(
        choices=Service.objects.values_list("name", "name"),
        widget=CheckboxSelectMultipleDropdown,
    )
    customer__name = filters.CharFilter(lookup_expr="icontains", label="Customer")
    pets__name = filters.CharFilter(lookup_expr="icontains", label="Pet")

    class Meta:
        model = Booking
        fields = []


class InvoiceFilter(FilterDefaults):
    state = filters.MultipleChoiceFilter(choices=Invoice.States.choices, widget=forms.CheckboxSelectMultiple)
    customer__name = filters.CharFilter(lookup_expr="icontains", label="Customer")

    class Meta:
        model = Invoice
        fields = [
            "state",
        ]


class VetFilter(FilterDefaults):
    customers__name = filters.CharFilter(lookup_expr="icontains", label="Customer")
    pets__name = filters.CharFilter(lookup_expr="icontains", label="Pet")
    name = filters.CharFilter(lookup_expr="icontains", label="Name")

    class Meta:
        model = Vet
        fields = ["name"]

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        return queryset.distinct()


class ServiceFilter(FilterDefaults):
    name = filters.CharFilter(lookup_expr="icontains")
    length = filters.DurationFilter()
    cost = filters.RangeFilter(widget=RangeInput)
    max_pet = filters.RangeFilter(widget=RangeInput)
    max_customer = filters.RangeFilter(widget=RangeInput)

    class Meta:
        model = Service
        fields = []
