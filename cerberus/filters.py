# Django
from django import forms

# Third Party
from django_filters import rest_framework as filters
from django_filters.widgets import RangeWidget

# Locals
from .models import Booking, Customer, Invoice, Pet, Service, Vet

ACTIVE_CHOICES = ((True, "Active"), (False, "Inactive"))


def strtobool(value: str) -> bool:
    return value.lower() in {"yes", "true", "y", "t", "1"}


class Switch(forms.widgets.Input):
    template_name = "forms/widgets/switch.html"
    input_type = "checkbox"


class RangeInput(RangeWidget):
    template_name = "forms/widgets/range_input.html"


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
    active = filters.TypedChoiceFilter(choices=ACTIVE_CHOICES, coerce=strtobool, widget=Switch)
    name = filters.CharFilter(lookup_expr="icontains", label="Name")
    pets__name = filters.CharFilter(lookup_expr="icontains", label="Pet")

    default_filters = {
        "active": True,
    }

    class Meta:
        model = Customer
        fields = ["active"]


class BookingFilter(FilterDefaults):
    from_date = filters.DateFilter(field_name="end", lookup_expr="gte")
    to_date = filters.DateFilter(field_name="start", lookup_expr="lte")
    on_date = filters.DateFilter(field_name="start", lookup_expr="date")
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
