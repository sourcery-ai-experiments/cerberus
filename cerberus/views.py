# Standard Library
from enum import Enum

# Django
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Model
from django.shortcuts import render
from django.urls import path
from django.utils.decorators import classonlymethod

# Third Party
from vanilla import CreateView, DeleteView, DetailView, GenericModelView, ListView, UpdateView

# Locals
from .forms import CustomerForm
from .models import Customer


@login_required
def dashboard(request):
    return render(request, "cerberus/dashboard.html", {})


class Actions(Enum):
    CREATE = CreateView
    DETAIL = DetailView
    UPDATE = UpdateView
    DELETE = DeleteView
    LIST = ListView


class CRUDViews(GenericModelView):
    model = Model

    @classonlymethod
    def get_defaults(cls):
        return {
            "paginate_by": 25,
        }

    @classonlymethod
    def as_view(cls, action: Actions):
        return type(
            f"{cls.model._meta.model_name}_list",
            (
                LoginRequiredMixin,
                action.value,
            ),
            {**cls.get_defaults(), **dict(cls.__dict__)},
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
