# Standard Library

# Django
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

# Locals
from ..filters import CustomerFilter, PetFilter, ServiceFilter, VetFilter
from ..forms import CustomerForm, PetForm, ServiceForm, VetForm
from ..models import Customer, Pet, Service, Vet
from .crud_views import CRUDViews


@login_required
def dashboard(request):
    return render(request, "cerberus/dashboard.html", {})


class CustomerCRUD(CRUDViews):
    model = Customer
    form_class = CustomerForm
    filter_class = CustomerFilter
    sortable_fields = ["name"]


class PetCRUD(CRUDViews):
    model = Pet
    form_class = PetForm
    filter_class = PetFilter
    sortable_fields = ["name", "customer"]


class VetCRUD(CRUDViews):
    model = Vet
    form_class = VetForm
    filter_class = VetFilter
    sortable_fields = ["name"]


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
