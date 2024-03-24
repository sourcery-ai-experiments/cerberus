# Standard Library
from collections.abc import Callable
from typing import Any

# Django
from django import forms

# Third Party
from djmoney.forms import MoneyWidget

# Locals
from .utils import rgetattr


class SingleMoneyWidget(MoneyWidget):
    def __init__(self, attrs=None, *args, **kwargs):
        attrs = attrs or {}
        attrs.update({"step": "any"})

        super().__init__(
            amount_widget=forms.NumberInput(attrs=attrs),  # type: ignore
            currency_widget=forms.HiddenInput(),
            *args,
            **kwargs,
        )

    def id_for_label(self, id_):
        return f"{id_}_0"


Attr_callback = Callable[[str, Any, int | str, dict[str, Any]], dict[str, Any] | None]


class SelectOptionAttrs(forms.Select):
    attr_callback: Attr_callback

    def __init__(self, attr_callback: Attr_callback, *args, **kwargs) -> None:
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
        option["attrs"] = self.attr_callback(name, value, label, option["attrs"])

        return option


class SelectDataAttrField(forms.Select):
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
            for model_field in self.model_fields:
                attr_value = rgetattr(value.instance, model_field, self.default_attr_value)
                if callable(attr_value):
                    attr_value = attr_value()

                attr_name = model_field.replace(".", "__")
                option["attrs"][f"data-{attr_name}"] = attr_value

        return option


class SelectDataOptionAttr(SelectOptionAttrs, SelectDataAttrField):
    def __init__(
        self,
        model_field: str,
        attr_callback: Attr_callback,
        default_attr_value: Any = None,
        *args,
        **kwargs,
    ):
        kwargs["model_field"] = model_field
        kwargs["default_attr_value"] = default_attr_value
        kwargs["attr_callback"] = attr_callback
        super().__init__(*args, **kwargs)