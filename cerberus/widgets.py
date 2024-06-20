# Standard Library
from collections.abc import Callable
from typing import Any

# Django
from django import forms
from django.forms import widgets
from django.utils.html import escape

# Third Party
from djmoney.forms import MoneyWidget

# Locals
from .utils import rgetattr


class TagsWidget(forms.TextInput):
    template_name = "forms/widgets/tags.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context.update({"tags": ",".join(f"'{escape(tag)}'" for tag in value or [])})

        return context


class SingleMoneyWidget(MoneyWidget):
    def __init__(self, attrs=None, *args, **kwargs):
        attrs = attrs or {}
        attrs.update({"x-mask:dynamic": "$money($input)", "x-data": ""})

        super().__init__(
            amount_widget=forms.TextInput(attrs=attrs),  # type: ignore
            currency_widget=forms.HiddenInput(),
            *args,
            **kwargs,
        )

    def id_for_label(self, id_):
        return f"{id_}_0"


Attr_callback = Callable[[str, Any, int | str, dict[str, Any]], dict[str, Any] | None]


class OptionAttrs(widgets.ChoiceWidget):
    attr_callback: Attr_callback | None

    def __init__(self, attr_callback: Attr_callback | None = None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.attr_callback = attr_callback

    def create_option(
        self,
        name: str,
        value: Any,
        label: int | str,
        selected: set[str] | bool,
        index: int,
        subindex: int | None = None,
        attrs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if self.attr_callback:
            option["attrs"] = self.attr_callback(name, value, label, option["attrs"])

        return option


class SelectOptionAttrs(OptionAttrs, forms.Select):
    pass


class DataAttrField(widgets.ChoiceWidget):
    model_fields: list[str]
    default_attr_value: Any

    def __init__(
        self,
        model_field: str | list[str],
        default_attr_value: Any = None,
        attrs=None,
        choices=(),
        *args,
        **kwargs,
    ):
        super().__init__(attrs, choices, *args, **kwargs)

        self.model_fields = model_field if isinstance(model_field, list) else [model_field]
        self.default_attr_value = default_attr_value

    def create_option(
        self,
        name: str,
        value: Any,
        label: int | str,
        selected: set[str] | bool,
        index: int,
        subindex: int | None = None,
        attrs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        option = super().create_option(name, value, label, selected, index, subindex, attrs)

        if value and hasattr(value, "instance"):
            instance = value.instance
            for model_field in self.model_fields:
                attr_value = rgetattr(instance, model_field, self.default_attr_value)
                if callable(attr_value):
                    attr_value = attr_value()

                attr_name = model_field.replace(".", "__")
                option["attrs"][f"data-{attr_name}"] = attr_value

        return option


class SelectDataAttrField(DataAttrField, forms.Select):
    pass


class SelectDataOptionAttr(OptionAttrs, DataAttrField, forms.Select):
    def __init__(
        self,
        model_field: str,
        attr_callback: Attr_callback | None = None,
        default_attr_value: Any = None,
        *args,
        **kwargs,
    ):
        kwargs["model_field"] = model_field
        kwargs["default_attr_value"] = default_attr_value
        kwargs["attr_callback"] = attr_callback
        super().__init__(*args, **kwargs)


class CheckboxDataOptionAttr(OptionAttrs, DataAttrField, forms.CheckboxSelectMultiple):
    def __init__(
        self,
        model_field: str,
        attr_callback: Attr_callback | None = None,
        default_attr_value: Any = None,
        *args,
        **kwargs,
    ):
        kwargs["model_field"] = model_field
        kwargs["default_attr_value"] = default_attr_value
        kwargs["attr_callback"] = attr_callback
        super().__init__(*args, **kwargs)


class CheckboxTable(forms.CheckboxSelectMultiple):
    model_fields: list[str]
    model_titles: list[str]

    crispy_template = "cerberus/widgets/checkbox_table.html"

    def __init__(self, model_fields: list[str], *args, **kwargs):
        self.model_fields = model_fields
        self.model_titles = [field.replace(".", " ").title() for field in model_fields]
        super().__init__(*args, **kwargs)

    def create_option(
        self,
        name: str,
        value: Any,
        label: int | str,
        selected: set[str] | bool,
        index: int,
        subindex: int | None = None,
        attrs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        option = super().create_option(name, value, label, selected, index, subindex, attrs)

        option["columns"] = {}
        if value and hasattr(value, "instance"):
            for model_field in self.model_fields:
                col_value = rgetattr(value.instance, model_field, None)
                if callable(col_value):
                    col_value = col_value()

                col_name = model_field.replace(".", "__")
                option["columns"][f"{col_name}"] = col_value

        return option
