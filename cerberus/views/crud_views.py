# Standard Library
from collections import namedtuple
from collections.abc import Iterable
from enum import Enum
from typing import Any, Protocol

# Django
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Model
from django.urls import path, reverse_lazy
from django.urls.resolvers import URLPattern

# Third Party
from django_filters import FilterSet
from vanilla import CreateView, DeleteView, DetailView, GenericModelView, ListView, UpdateView


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
                sort_order = self.request.GET.get("sort_order", "desc")

                if callable(getattr(self.model, f"sort_{sort}", None)):
                    queryset = getattr(self.model, f"sort_{sort}")(queryset, sort_order)
                else:
                    sort_order_symbol = "-" if sort_order == "desc" else ""
                    queryset = queryset.order_by(f"{sort_order_symbol}{sort}")

            elif sort != "None":
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

        def list_crumb() -> Crumb:
            return Crumb(verbose_name_plural, reverse_lazy(f"{model_name}_{Actions.LIST.value}"))

        def detail_crumb() -> Crumb:
            return Crumb(str(obj), reverse_lazy(f"{model_name}_{Actions.DETAIL.value}", kwargs={"pk": obj_id}))

        def update_crumb() -> Crumb:
            return Crumb("Edit", reverse_lazy(f"{model_name}_{Actions.UPDATE.value}", kwargs={"pk": obj_id}))

        def create_crumb() -> Crumb:
            return Crumb("Create", reverse_lazy(f"{model_name}_{Actions.CREATE.value}", kwargs={"pk": obj_id}))

        def delete_crumb() -> Crumb:
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


def extra_view(
    detail: bool,
    methods: list[str] | None = None,
    url_path: str | None = None,
    url_name: str | None = None,
    **kwargs,
):
    methods = ["get"] if methods is None else methods
    methods = [method.lower() for method in methods]

    def decorator(func):
        func.methods = methods
        func.detail = detail
        func.url_path = url_path or func.__name__.replace("_", "-")
        func.url_name = url_name

        return func

    return decorator


class EditViewProtocol(Protocol):
    def form_valid(self, form): ...

    def form_invalid(self, form): ...


class SafeFormSave:
    def form_valid(self: EditViewProtocol, form):
        try:
            with transaction.atomic():
                return super().form_valid(form)
        except (ValueError, ValidationError) as exception:
            errors = exception if isinstance(exception, Iterable) else [exception]
            for error in errors:
                form.add_error(None, str(error))

            return self.form_invalid(form)


class CRUDViews(GenericModelView):
    model = Model
    delete_success_url: str | None = None
    requires_login: bool = True
    extra_requires_login: bool | None = None

    lookup_field: str = "pk"

    extra_mixins: list = []

    @classmethod
    def url_lookup(cls) -> str:
        if cls.lookup_field == "pk" and cls.model._meta.pk:
            real_lookup_field = cls.model._meta.pk.name
        else:
            real_lookup_field = cls.lookup_field

        prefix = "str"
        match cls.model._meta.get_field(real_lookup_field).get_internal_type():
            case "BigAutoField":
                prefix = "int"
            case "UUIDField":
                prefix = "uuid"

        return f"<{prefix}:{cls.lookup_field}>"

    @classmethod
    def url_parts(cls) -> dict[Actions, str]:
        return {
            Actions.CREATE: "create",
            Actions.DETAIL: f"{cls.url_lookup()}",
            Actions.UPDATE: f"{cls.url_lookup()}/edit",
            Actions.DELETE: f"{cls.url_lookup()}/delete",
            Actions.LIST: "",
        }

    @classmethod
    def get_defaults(cls, action: Actions) -> dict[str, Any]:
        defaults: dict[str, Any] = {
            "paginate_by": 25,
        }

        match action:
            case Actions.DELETE:
                defaults["success_url"] = cls.delete_success_url or reverse_lazy(f"{cls.model._meta.model_name}_list")

        if cls.lookup_field:
            defaults["lookup_field"] = cls.lookup_field

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
                    SafeFormSave if action in [Actions.CREATE, Actions.UPDATE] else None,
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
        url_parts = cls.url_parts()

        paths = [
            path(
                f"{model_name}/{url_parts[action]}",
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

    def get_breadcrumbs(self, obj: Model | None) -> list[Crumb]:
        model_name = self.model._meta.model_name or ""
        verbose_name_plural = (self.model._meta.verbose_name_plural or "").title()

        list_name = f"{model_name}_{Actions.LIST.value}"
        detail_name = f"{model_name}_{Actions.DETAIL.value}"

        crumbs = [
            Crumb("Dashboard", reverse_lazy("dashboard")),
            Crumb(verbose_name_plural, reverse_lazy(list_name)),
            Crumb(str(obj), reverse_lazy(detail_name, kwargs={"pk": obj.pk})) if obj else None,
        ]

        return [crumb for crumb in crumbs if crumb is not None]

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

                view_func = getattr(cls(), name)
                url_name = view.url_name or f"{model_name}_{view.__name__}"
                if cls._extra_requires_login():
                    view_func = login_required(view_func)

                views.append(path(route, view_func, name=url_name))  # type: ignore

        return views
