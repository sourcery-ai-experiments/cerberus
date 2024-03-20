# Standard Library
from typing import Any

# Django
from django import forms
from django.db.models import Model

# Third Party
from djmoney.forms import MoneyWidget

# Locals
from .models import Booking, Charge, Customer, Invoice, Pet, Service, Vet


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


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            "first_name",
            "last_name",
            "other_names",
            "invoice_address",
            "invoice_email",
            "active",
            "vet",
            "tags",
        ]
        widgets = {"tags": forms.TextInput()}


class PetForm(forms.ModelForm):
    class Meta:
        model = Pet
        fields = [
            "name",
            "dob",
            "active",
            "social_media_concent",
            "sex",
            "description",
            "neutered",
            "medical_conditions",
            "treatment_limit",
            "allergies",
            "tags",
            "customer",
            "vet",
        ]


class VetForm(forms.ModelForm):
    class Meta:
        model = Vet
        fields = [
            "name",
            "phone",
            "details",
        ]


class DataAttrSelect(forms.Select):
    model_field: str
    _model: Model | None = None
    default_attr_value: Any

    def __init__(
        self,
        model_field: str,
        model: Model | None = None,
        default_attr_value: Any = None,
        attrs=None,
        choices=(),
        *args,
        **kwargs,
    ):
        super().__init__(attrs, choices, *args, **kwargs)
        self.model_field = model_field
        self._model = model
        self.default_attr_value = default_attr_value

    def linked_model(self) -> Model:
        if self._model is None:
            try:
                self._model = self.choices.queryset.model
            except AttributeError:
                raise ValueError("Model not set and could not be inferred from queryset")

        return self._model

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
        if value:
            object = self.linked_model().objects.get(pk=f"{value}")
            option["attrs"][f"data-{self.model_field}"] = getattr(object, self.model_field, self.default_attr_value)

        return option


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = [
            "service",
            "cost",
            "pet",
            "start",
            "end",
        ]
        widgets = {
            "state": forms.TextInput(attrs={"readonly": True}),
            "service": DataAttrSelect("cost_value"),
        }


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            "details",
            "due",
            "adjustment",
            "customer_name",
            "sent_to",
            "invoice_address",
            "send_notes",
        ]
        widgets = {
            "adjustment": SingleMoneyWidget(),
            "due": forms.DateInput(attrs={"type": "date"}),
        }


class ChargeForm(forms.ModelForm):
    class Meta:
        model = Charge
        fields = ["name", "line", "quantity"]
        widgets = {
            "line": SingleMoneyWidget(attrs={"x-model.number.fill": "line", "min": "0"}),
            "quantity": forms.NumberInput(attrs={"x-model.number.fill": "quantity"}),
        }


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = [
            "name",
            "length",
            "booked_length",
            "cost",
            "cost_per_additional",
            "max_pet",
            "max_customer",
            "display_colour",
        ]
        widgets = {
            "cost": SingleMoneyWidget(),
            "cost_per_additional": SingleMoneyWidget(),
            "display_colour": forms.TextInput(attrs={"type": "color"}),
        }
