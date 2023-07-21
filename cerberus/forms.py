# Django
from django import forms

# Third Party
from djmoney.forms import MoneyWidget

# Locals
from .models import Booking, Charge, Customer, Invoice, Pet, Vet


class SingleMoneyWidget(MoneyWidget):
    def __init__(self, attrs={}, *args, **kwargs):
        super().__init__(
            amount_widget=forms.NumberInput(
                attrs={
                    **{
                        "step": "any",
                    },
                    **attrs,
                }
            ),
            currency_widget=forms.HiddenInput(),
            *args,
            **kwargs,
        )


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = "__all__"
        # fields = ["first_name","last_name","other_names","invoice_address","invoice_email"]
        widgets = {"tags": forms.TextInput()}


class PetForm(forms.ModelForm):
    class Meta:
        model = Pet
        fields = "__all__"


class VetForm(forms.ModelForm):
    class Meta:
        model = Vet
        fields = "__all__"


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = "__all__"
        exclude = ["booking_slot"]
        widgets = {"state": forms.TextInput(attrs={"readonly": True})}


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        exclude = ["paid_on", "sent_on", "state", "sent_to", "created", "last_updated"]
        widgets = {"adjustment": SingleMoneyWidget()}


class ChargeForm(forms.ModelForm):
    class Meta:
        model = Charge
        fields = ["name", "line", "quantity"]
        widgets = {
            "line": SingleMoneyWidget(attrs={"x-model.number.fill": "line", "min": "0"}),
            "quantity": forms.NumberInput(attrs={"x-model.number.fill": "quantity"}),
        }
