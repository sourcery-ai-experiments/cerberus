# Standard Library
from enum import Enum
from typing import Any

# Django
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Model
from django.shortcuts import render
from django.urls import path, reverse_lazy
from django.utils.decorators import classonlymethod

# Third Party
from vanilla import CreateView
from vanilla import DeleteView as DeleteView
from vanilla import DetailView, GenericModelView, ListView, UpdateView

# Locals
from .forms import CustomerForm, InvoiceForm, PetForm
from .models import Customer, Invoice, Pet


@login_required
def dashboard(request):
    return render(request, "cerberus/dashboard.html", {})


class Actions(Enum):
    CREATE = "create"
    DETAIL = "detail"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"


class CRUDViews(GenericModelView):
    model = Model
    delete_success_url: str | None = None

    @classonlymethod
    def get_defaults(cls, action: Actions) -> dict[str, Any]:
        defaults: dict[str, Any] = {
            "paginate_by": 25,
        }

        match action:
            case Actions.DELETE:
                defaults["success_url"] = cls.delete_success_url or reverse_lazy(f"{cls.model._meta.model_name}_list")

        return defaults

    @classonlymethod
    def get_view_class(cls, action: Actions):
        match action:
            case Actions.CREATE:
                return CreateView
            case Actions.DETAIL:
                return DetailView
            case Actions.UPDATE:
                return UpdateView
            case Actions.DELETE:
                return DeleteView
            case Actions.LIST:
                return ListView
            case _:
                raise Exception(f"Unhandled action {action}")

    @classonlymethod
    def as_view(cls, action: Actions):
        actionClass = cls.get_view_class(action)
        return type(
            f"{cls.model._meta.model_name}_{action.name.lower()}",
            (
                LoginRequiredMixin,
                actionClass,
            ),
            {**cls.get_defaults(action), **dict(cls.__dict__)},
        ).as_view()

    @classonlymethod
    def get_urls(cls):
        model_name = cls.model._meta.model_name

        urlpatterns = [
            path(f"{model_name}/", cls.as_view(action=Actions.LIST), name=f"{model_name}_list"),
            path(f"{model_name}/new/", cls.as_view(action=Actions.CREATE), name=f"{model_name}_create"),
            path(f"{model_name}/<int:pk>/", cls.as_view(action=Actions.DETAIL), name=f"{model_name}_detail"),
            path(f"{model_name}/<int:pk>/edit/", cls.as_view(action=Actions.UPDATE), name=f"{model_name}_update"),
            path(f"{model_name}/<int:pk>/delete/", cls.as_view(action=Actions.DELETE), name=f"{model_name}_delete"),
        ]
        return urlpatterns


class CustomerCRUD(CRUDViews):
    model = Customer
    form_class = CustomerForm


class PetCRUD(CRUDViews):
    model = Pet
    form_class = PetForm


class InvoiceCRUD(CRUDViews):
    model = Invoice
    form_class = InvoiceForm

    @classonlymethod
    def get_view_class(cls, action: Actions):
        match action:
            case Actions.UPDATE:
                return UpdateView
            case _:
                return super().get_view_class(action)
