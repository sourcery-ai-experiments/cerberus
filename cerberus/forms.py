# Standard Library

# Django
from django import forms

# Locals
from .models import Booking, Charge, Customer, Invoice, Pet, Service, Vet
from .utils import minimize_whitespace
from .widgets import SelectDataAttrField, SelectDataOptionAttr, SingleMoneyWidget


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


class BookingForm(forms.ModelForm):
    attributes = {
        "x-data": "{cost: '', cost_changed: false, customer: false, pet: false, start: '', end: '' }",
    }

    customer = forms.ModelChoiceField(
        Customer.objects.all(),
        widget=forms.Select(
            attrs={
                "x-model": "customer",
                "@change": minimize_whitespace(
                    """
                const pets = document.querySelectorAll(`option[data-customer__id="${customer}"]`);
                pet = pets.length == 1 ? pets[0].value : false;
"""
                ),
            }
        ),
    )

    class Meta:
        model = Booking
        fields = [
            "service",
            "cost",
            "customer",
            "pet",
            "start",
            "end",
        ]
        widgets = {
            "state": forms.TextInput(attrs={"readonly": True}),
            "cost": SingleMoneyWidget(
                attrs={
                    "x-model": "cost",
                    "@change": "cost_changed = $event.target.value !== ''",
                }
            ),
            "pet": SelectDataOptionAttr(
                "customer.id",
                attrs={
                    ":disabled": "!customer",
                    "x-model": "pet",
                },
                attr_callback=(
                    lambda name, value, label, attrs: {
                        **attrs,
                        ":class": "customer != $el.dataset.customer__id ? 'hidden' : ''",
                    }
                ),
            ),
            "service": SelectDataAttrField(
                "cost_amount",
                attrs={
                    "@change": minimize_whitespace(
                        """
                        if (!cost_changed) {
                            $nextTick(() => cost = $event.target.options[$event.target.selectedIndex].dataset.cost_amount);
                            cost_changed = false;
                        }
"""
                    ),
                },
            ),
            "start": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                    "step": 900,
                    "x-model": "start",
                    "@change": "start = roundTime(start)",
                }
            ),
            "end": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                    "step": 900,
                    "x-model": "end",
                    "@change": "end = roundTime(end)",
                }
            ),
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
