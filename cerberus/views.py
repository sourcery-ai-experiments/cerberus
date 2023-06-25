from django.http import HttpResponse
from django.shortcuts import render
from vanilla import ListView, DetailView, GenericModelView, CreateView, DeleteView, UpdateView
from enum import Enum
from django.utils.decorators import classonlymethod
from django.urls import path, reverse
from django.db.models import Model

from .models import Customer


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

    @classonlymethod
    def as_view(cls, action: Actions):
        model_name = cls.model._meta.model_name
        match action:
            case Actions.LIST:
                base_cls = ListView
            case Actions.DETAIL:
                base_cls = DetailView
            case Actions.UPDATE:
                base_cls = UpdateView
            case Actions.DELETE:
                base_cls = DeleteView
            case Actions.CREATE:
                base_cls = CreateView
            case _:
                raise NotImplemented(f"{action} not implemented yet")

        return type(f"{model_name}_list", (base_cls, ), dict(cls.__dict__)).as_view()

    @classonlymethod
    def get_urls(cls):
        model_name = cls.model._meta.model_name
        urlpatterns = [
            path(f"{model_name}/", cls.as_view(action=Actions.LIST), name=f"{model_name}_list"),
            path(f"{model_name}/new/", cls.as_view(action=Actions.CREATE), name=f"{model_name}-create"),
            path(f"{model_name}/<int:pk>/", cls.as_view(action=Actions.DETAIL), name=f"{model_name}_detail"),
            path(f"{model_name}/<int:pk>/edit/", cls.as_view(action=Actions.UPDATE), name=f"{model_name}-update"),
            path(f"{model_name}/<int:pk>/delete/", cls.as_view(action=Actions.DELETE), name=f"{model_name}-delete"),
        ]
        return urlpatterns

class CustomerCRUD(CRUDViews):
    model = Customer
