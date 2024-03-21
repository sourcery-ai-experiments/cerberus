# Standard Library
from typing import Any

# Django
from django import forms

# Third Party
from djmoney.forms import MoneyWidget

# Locals
from .utils import rgetattr


class SingleMoneyWidget(MoneyWidget):
    def __init__(self, attrs=None, *args, **kwargs):
        if attrs is None:
            attrs = {}
        super().__init__(
            amount_widget=forms.NumberInput(
                attrs={
                    **{
                        "step": "any",
                    },
                    **attrs,
                }
            ),  # type: ignore
            currency_widget=forms.HiddenInput(),
            *args,
            **kwargs,
        )

    def id_for_label(self, id_):
        return f"{id_}_0"


class DataAttrSelect(forms.Select):
    model_field: str
    attr_name: str
    default_attr_value: Any

    def __init__(
        self,
        model_field: str,
        default_attr_value: Any = None,
        attrs=None,
        choices=(),
        *args,
        **kwargs,
    ):
        super().__init__(attrs, choices, *args, **kwargs)
        self.model_field = model_field
        self.attr_name = model_field.replace(".", "__")
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
            value = rgetattr(value.instance, self.model_field, self.default_attr_value)
            if callable(value):
                value = value()

            option["attrs"][f"data-{self.attr_name}"] = value

        return option
