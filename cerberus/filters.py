# Standard Library
from distutils.util import strtobool

# Django
from django import forms
from django.db.models import Value
from django.db.models.functions import Concat

# Third Party
from django_filters import rest_framework as filters

# Locals
from .models import Booking, Customer, Invoice, Pet, Vet

ACTIVE_CHOICES = ((True, "Active"), (False, "Inactive"))


class Switch(forms.widgets.Input):
    template_name = "forms/widgets/switch.html"
    input_type = "checkbox"


class CustomerMixin:
    def customer_name_filter(self, queryset, name, value):
        return queryset.annotate(customer__name=Concat("customer__first_name", Value(" "), "customer__last_name")).filter(
            customer__name__contains=value
        )


class FilterDefaults(filters.FilterSet):
    default_filters = {}

    def __init__(self, data=None, *args, **kwargs):
        if data is not None:
            data = data.copy()
            for key, value in self.default_filters.items():
                if key not in data:
                    data[key] = value

        super().__init__(data, *args, **kwargs)


class PetFilter(FilterDefaults, CustomerMixin):
    active = filters.TypedChoiceFilter(choices=ACTIVE_CHOICES, coerce=strtobool, widget=Switch)
    name = filters.CharFilter(lookup_expr="icontains", label="Name")
    customer = filters.CharFilter(method="customer_name_filter")

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


class BookingFilter(filters.FilterSet):
    from_date = filters.DateFilter(field_name="end", lookup_expr="gte")
    to_date = filters.DateFilter(field_name="start", lookup_expr="lte")
    on_date = filters.DateFilter(field_name="start", lookup_expr="date")

    class Meta:
        model = Booking
        fields = []


class InvoiceFilter(filters.FilterSet, CustomerMixin):
    state = filters.MultipleChoiceFilter(choices=Invoice.States.choices, widget=forms.CheckboxSelectMultiple)
    customer = filters.CharFilter(method="customer_name_filter")

    class Meta:
        model = Invoice
        fields = [
            "state",
        ]


class VetFilter(filters.FilterSet, CustomerMixin):
    customer = filters.CharFilter(method="customer_name_filter", label="Customer")
    pets__name = filters.CharFilter(lookup_expr="icontains", label="Pet")
    name = filters.CharFilter(lookup_expr="icontains", label="Name")

    class Meta:
        model = Vet
        fields = ["name"]

    def customer_name_filter(self, queryset, name, value):
        return queryset.annotate(customers__name=Concat("customers__first_name", Value(" "), "customers__last_name")).filter(
            customers__name__contains=value
        )
