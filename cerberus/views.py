# Standard Library
from collections import namedtuple
from enum import Enum
from typing import Any

# Django
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Model
from django.forms import modelformset_factory
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse_lazy
from django.utils.decorators import classonlymethod
from django.views import View

# Third Party
from django_filters import FilterSet
from vanilla import CreateView, DeleteView, DetailView, GenericModelView, ListView, UpdateView

# Locals
from .filters import CustomerFilter, InvoiceFilter, PetFilter, VetFilter
from .forms import BookingForm, ChargeForm, CustomerForm, InvoiceForm, PetForm, VetForm
from .models import Booking, Charge, Customer, Invoice, Pet, Vet


@login_required
def dashboard(request):
    return render(request, "cerberus/dashboard.html", {})


class Actions(Enum):
    CREATE = "create"
    DETAIL = "detail"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"


Crumb = namedtuple("Crumb", ["name", "url"])


class DefaultTemplateMixin(GenericModelView):
    def get_template_names(self):
        defaults = [f"{self.model._meta.app_label}/default{self.template_name_suffix}.html"] if self.model else []
        return super().get_template_names() + defaults


class FilterableMixin(GenericModelView):
    filter_class: FilterSet | None

    def get_filter(self):
        return self.filter_class

    def get_queryset(self):
        queryset = super().get_queryset()

        if filter_class := getattr(self, "filter_class", None):
            return filter_class(self.request.GET, queryset).qs

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        queryset = self.get_queryset()
        if filter_class := getattr(self, "filter_class", None):
            context["filter"] = filter_class(self.request.GET, queryset)

        return context


class BreadcrumbMixin(GenericModelView):
    def get_breadcrumbs(self):
        crumbs = [
            Crumb("Dashboard", reverse_lazy("dashboard")),
        ]

        model_name = self.model._meta.model_name if self.model else ""
        verbose_name_plural = self.model._meta.verbose_name_plural.title() if self.model else ""

        obj = getattr(self, "object", None)
        obj_id = getattr(obj, "id", 0)

        def list_crumb():
            return Crumb(verbose_name_plural, reverse_lazy(f"{model_name}_{Actions.LIST.value}"))

        def detail_crumb():
            return Crumb(str(obj), reverse_lazy(f"{model_name}_{Actions.DETAIL.value}", kwargs={"pk": obj_id}))

        def update_crumb():
            return Crumb("Edit", reverse_lazy(f"{model_name}_{Actions.UPDATE.value}", kwargs={"pk": obj_id}))

        def create_crumb():
            return Crumb("Create", reverse_lazy(f"{model_name}_{Actions.CREATE.value}", kwargs={"pk": obj_id}))

        def delete_crumb():
            return Crumb("Delete", reverse_lazy(f"{model_name}_{Actions.DELETE.value}", kwargs={"pk": obj_id}))

        match self.__class__.__name__.split("_"):
            case _, Actions.LIST.value:
                crumbs += [list_crumb()]
            case _, Actions.DETAIL.value:
                crumbs += [list_crumb(), detail_crumb()]
            case _, Actions.UPDATE.value:
                crumbs += [list_crumb(), detail_crumb(), update_crumb()]
            case _, Actions.CREATE.value:
                crumbs += [list_crumb(), create_crumb()]
            case _, Actions.DELETE.value:
                crumbs += [list_crumb(), detail_crumb(), delete_crumb()]

        return list(filter(lambda crumb: crumb is not None, crumbs))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = self.get_breadcrumbs()

        return context


class ActionView(View):
    model = Model
    field = str

    def get(self, request, pk: int, action: str):
        model = get_object_or_404(self.model, pk=pk)
        transitions = getattr(model, f"get_all_{self.field}_transitions")()
        available_transitions = getattr(model, f"get_all_{self.field}_transitions")()

        if action not in [t.name for t in transitions]:
            raise Http404(f"{action} is not a valid action on {self.model._meta.model_name}")

        if action not in [t.name for t in available_transitions]:
            raise Http404(f"{action} is not currently available on {self.model._meta.model_name}")

        getattr(model, action)()
        redirect_url = getattr(model, "get_absolute_url", lambda: "/")()

        return redirect(redirect_url)


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
            f"{cls.model._meta.model_name}_{action.value}",
            (
                LoginRequiredMixin,
                BreadcrumbMixin,
                FilterableMixin,
                DefaultTemplateMixin,
                actionClass,
            ),
            {**cls.get_defaults(action), **dict(cls.__dict__)},
        ).as_view()

    @classonlymethod
    def get_urls(cls):
        model_name = cls.model._meta.model_name

        return [
            path(
                f"{model_name}/",
                cls.as_view(action=Actions.LIST),
                name=f"{model_name}_{Actions.LIST.value}",
            ),
            path(
                f"{model_name}/new/",
                cls.as_view(action=Actions.CREATE),
                name=f"{model_name}_{Actions.CREATE.value}",
            ),
            path(
                f"{model_name}/<int:pk>/",
                cls.as_view(action=Actions.DETAIL),
                name=f"{model_name}_{Actions.DETAIL.value}",
            ),
            path(
                f"{model_name}/<int:pk>/edit/",
                cls.as_view(action=Actions.UPDATE),
                name=f"{model_name}_{Actions.UPDATE.value}",
            ),
            path(
                f"{model_name}/<int:pk>/delete/",
                cls.as_view(action=Actions.DELETE),
                name=f"{model_name}_{Actions.DELETE.value}",
            ),
        ]


class CustomerCRUD(CRUDViews):
    model = Customer
    form_class = CustomerForm
    filter_class = CustomerFilter


class PetCRUD(CRUDViews):
    model = Pet
    form_class = PetForm
    filter_class = PetFilter


class VetCRUD(CRUDViews):
    model = Vet
    form_class = VetForm
    filter_class = VetFilter


class BookingCRUD(CRUDViews):
    model = Booking
    form_class = BookingForm


class BookingStateActions(ActionView):
    model = Booking
    field = "state"


class InvoiceList(ListView):
    def get_queryset(self):
        return super().get_queryset()


class InvoiceUpdate(UpdateView):
    def get_success_url(self):
        return reverse_lazy("invoice_detail", kwargs={"pk": self.object.id})

    def get_formset(self):
        return modelformset_factory(Charge, form=ChargeForm, extra=1)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        formset = self.get_formset()
        context["formset"] = formset(queryset=context["object"].charges.all())

        return context

    def post(self, request, *args, **kwargs):
        formset = self.get_formset()(data=request.POST, files=request.FILES)
        if formset.is_valid():
            formset.save()
            return super().post(request, *args, **kwargs)

        form = self.get_form(
            data=request.POST,
            files=request.FILES,
            instance=self.object,
        )
        return self.form_invalid(form)


class InvoiceCRUD(CRUDViews):
    model = Invoice
    form_class = InvoiceForm
    filter_class = InvoiceFilter

    @classonlymethod
    def get_view_class(cls, action: Actions):
        match action:
            case Actions.UPDATE:
                return InvoiceUpdate
            case _:
                return super().get_view_class(action)


@login_required
def pdf(request, pk: int):
    invoice: Invoice = get_object_or_404(Invoice, pk=pk)

    return invoice.get_pdf_response()
