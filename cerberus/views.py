# Standard Library
from collections import namedtuple
from enum import Enum
from typing import Any

# Django
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Model
from django.forms import modelformset_factory
from django.http import Http404, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse_lazy
from django.urls.resolvers import URLPattern
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
    model_name: str

    @classmethod
    def create_class(cls, model_name: str) -> type:
        return type(f"{model_name.capitalize()}{cls.__name__}", (cls,), {"model_name": model_name})

    def get_template_names(self):
        defaults = [f"{self.model._meta.app_label}/default{self.template_name_suffix}.html"] if self.model else []
        return super().get_template_names() + defaults

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["model_name"] = self.model_name
        context["route_names"] = {a.value: f"{self.model_name}_{a.value}" for a in Actions}

        return context


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


class SortableFieldError(Exception):
    pass


class SortableViewMixin(GenericModelView):
    sortable_fields: list[str] = []

    def get_queryset(self):
        queryset = super().get_queryset()

        if sort := self.request.GET.get("sort"):
            if sort in self.sortable_fields:
                sort_order = "-" if self.request.GET.get("sort_order", "desc") == "desc" else ""
                queryset = queryset.order_by(f"{sort_order}{sort}")
            else:
                raise SortableFieldError(
                    f"Invalid sort field '{sort}', must be one of {', '.join(self.sortable_fields)}"
                )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["sortable_fields"] = self.sortable_fields
        context["sort"] = self.request.GET.get("sort")
        context["sort_order"] = self.request.GET.get("sort_order")
        context["alt_sort_order"] = "asc" if context["sort_order"] == "desc" else "desc"

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


class TransitionView(View):
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


def extra_view(detail: bool, methods=None, url_path=None, url_name=None, **kwargs):
    methods = ["get"] if methods is None else methods
    methods = [method.lower() for method in methods]

    def decorator(func):
        func.methods = methods
        func.detail = detail
        func.url_path = url_path or func.__name__.replace("_", "-")
        func.url_name = url_name

        return func

    return decorator


class CRUDViews(GenericModelView):
    model = Model
    delete_success_url: str | None = None
    requires_login: bool = True
    extra_requires_login: bool | None = None

    url_lookup: str = "<int:pk>"
    url_parts: dict[Actions, str] = {
        Actions.CREATE: "create",
        Actions.DETAIL: f"{url_lookup}",
        Actions.UPDATE: f"{url_lookup}/edit",
        Actions.DELETE: f"{url_lookup}/delete",
        Actions.LIST: "",
    }

    extra_mixins: list = []

    @classmethod
    def get_defaults(cls, action: Actions) -> dict[str, Any]:
        defaults: dict[str, Any] = {
            "paginate_by": 25,
        }

        match action:
            case Actions.DELETE:
                defaults["success_url"] = cls.delete_success_url or reverse_lazy(f"{cls.model._meta.model_name}_list")

        return defaults

    @classmethod
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

    @classmethod
    def _get_class_basses(cls, view, action: Actions):
        return tuple(
            filter(
                lambda m: m is not None,
                [
                    LoginRequiredMixin if cls.requires_login else None,
                    BreadcrumbMixin,
                    FilterableMixin if action == Actions.LIST else None,
                    SortableViewMixin if action == Actions.LIST else None,
                    DefaultTemplateMixin.create_class(cls.model_name()),
                    view,
                ]
                + cls.extra_mixins,
            )
        )

    @classmethod
    def as_view(cls, action: Actions):
        action_class = cls.get_view_class(action)
        return type(
            f"{cls.model._meta.model_name}_{action.value}",
            cls._get_class_basses(action_class, action),
            {**cls.get_defaults(action), **dict(cls.__dict__)},
        ).as_view()

    @classmethod
    def model_name(cls):
        return cls.model._meta.model_name or cls.model.__class__.__name__.lower()

    @classmethod
    def get_urls(cls):
        model_name = cls.model_name()

        paths = [
            path(
                f"{model_name}/{cls.url_parts[action]}",
                cls.as_view(action),
                name=f"{model_name}_{action.value}",
            )
            for action in Actions
        ]
        return paths + cls.extra_views(model_name)

    @classmethod
    def _extra_requires_login(cls):
        if cls.extra_requires_login is None:
            return cls.requires_login
        return cls.extra_requires_login

    @classmethod
    def extra_views(cls, model_name: str) -> list[URLPattern]:
        views: list[URLPattern] = []
        for name in dir(cls):
            view = getattr(cls, name)
            if all(hasattr(view, attr) for attr in ["methods", "detail", "url_path", "url_name"]):
                if view.detail:
                    route = f"{model_name}/<int:pk>/{view.url_path}/"
                else:
                    route = f"{model_name}/{view.url_path}/"

                url_name = view.url_name or f"{model_name}_{view.__name__}"
                view_func = getattr(cls(), name)
                if cls._extra_requires_login():
                    view_func = login_required(view_func)

                views.append(path(route, view_func, name=url_name))  # type: ignore

        return views


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


class BookingCRUD(CRUDViews):
    model = Booking
    form_class = BookingForm
    sortable_fields = ["pet__customer", "pet", "service", "start"]


class BookingStateActions(TransitionView):
    model = Booking
    field = "state"


class InvoiceUpdateView(UpdateView):
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


class InvoiceCreateView(CreateView):
    def get(self, request, *args, **kwargs):
        form = self.get_form(initial={k: str(v) for k, v in request.GET.items()})
        context = self.get_context_data(form=form)
        return self.render_to_response(context)


class InvoiceCRUD(CRUDViews):
    model = Invoice
    form_class = InvoiceForm
    filter_class = InvoiceFilter
    sortable_fields = ["id", "customer", "total"]

    @classmethod
    def get_view_class(cls, action: Actions):
        match action:
            case Actions.UPDATE:
                return InvoiceUpdateView
            case Actions.CREATE:
                return InvoiceCreateView
            case _:
                return super().get_view_class(action)

    @extra_view(detail=True, methods=["get", "post"])
    def email(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)
        if request.method != "POST":
            return render(request, "cerberus/invoice_email_confirm.html", {"object": invoice, "invoice": invoice})
        try:
            invoice.resend_email()
        except AssertionError as e:
            return HttpResponseNotAllowed(f"Email not sent: {e}")

        return render(request, "cerberus/invoice_email_sent.html", {"object": invoice, "invoice": invoice})

    @extra_view(detail=True, methods=["get"], url_name="invoice_pdf")
    def download(self, request, pk: int):
        invoice: Invoice = get_object_or_404(Invoice, pk=pk)

        return invoice.get_pdf_response()
