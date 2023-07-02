# Django
from django import forms

# Third Party
from djmoney.forms import MoneyWidget

# Locals
from .models import Charge, Customer, Invoice, Pet


class MoneyInput(forms.NumberInput):
    template_name = "cerberus/widgets/money_input.html"


class SingleMoneyWidget(MoneyWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(
            amount_widget=MoneyInput(attrs={"step": "0.01", "min": "0"}), currency_widget=forms.HiddenInput(), *args, **kwargs
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


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        # fields = "__all__"
        exclude = ["paid_on", "sent_on", "state", "sent_to", "created", "last_updated"]
        widgets = {"adjustment": SingleMoneyWidget()}


class ChargeForm(forms.ModelForm):
    class Meta:
        model = Charge
        fields = ["name", "line", "quantity"]
        widgets = {"line": SingleMoneyWidget()}
