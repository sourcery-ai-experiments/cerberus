# Django
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

# Locals
from ..filters import ServiceFilter, VetFilter
from ..forms import ServiceForm, VetForm
from ..models import Service, Vet
from .crud_views import CRUDViews


@login_required
def dashboard(request):
    context = {}
    return render(request, "cerberus/dashboard.html", context)


class VetCRUD(CRUDViews):
    model = Vet
    form_class = VetForm
    filter_class = VetFilter
    sortable_fields = ["name"]
    lookup_field = "sqid"


class ServiceCRUD(CRUDViews):
    model = Service
    form_class = ServiceForm
    filter_class = ServiceFilter
    sortable_fields = [
        "name",
        "length",
        "cost",
        "cost_per_additional",
        "max_pet",
        "max_customer",
        "display_colour",
    ]
    lookup_field = "slug"
