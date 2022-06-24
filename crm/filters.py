# Standard Library

# Django

# Third Party
from django_filters import rest_framework as filters

# Locals
from .models import Booking, Customer, Pet


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
    default_filters = {
        "active": True,
    }

    class Meta:
        model = Pet
        fields = ["active"]


class CustomerFilter(FilterDefaults):
    default_filters = {
        "active": True,
    }

    class Meta:
        model = Customer
        fields = ["active"]


class BookingFilter(filters.FilterSet):
    from_date = filters.DateFilter(field_name="end", lookup_expr="gte")
    to_date = filters.DateFilter(field_name="start", lookup_expr="lte")

    class Meta:
        model = Booking
        fields = []
