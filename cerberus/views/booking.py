# Standard Library

# Django
from django.shortcuts import render

# Locals
from ..forms import BookingForm
from ..models import Booking
from .crud_views import CRUDViews, extra_view
from .transition_view import TransitionView


class BookingCRUD(CRUDViews):
    model = Booking
    form_class = BookingForm
    sortable_fields = ["pet__customer", "pet", "service", "start", "length"]

    @extra_view(detail=False, methods=["get"])
    def test(self, request):
        return render(request, "cerberus/booking_test.html", {})


class BookingStateActions(TransitionView):
    model = Booking
    field = "state"
