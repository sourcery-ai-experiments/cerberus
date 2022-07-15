# Standard Library

# Django
from django.shortcuts import get_object_or_404, render  # noqa
from django.views.generic import DetailView, ListView

# Locals
from .models import Customer, Pet, Vet


class CustomerListView(ListView):
    model = Customer
    context_object_name = "customers"


class CustomerEditView(DetailView):
    model = Customer
    context_object_name = "customer"


class PetListView(ListView):
    model = Pet
    context_object_name = "pets"


class VetListView(ListView):
    model = Vet
    context_object_name = "vets"
