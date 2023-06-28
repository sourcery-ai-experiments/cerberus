# Django
from django import forms

# Locals
from .models import Customer, Pet


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = "__all__"
        # fields = ["first_name","last_name","other_names","invoice_address","invoice_email"]


class PetForm(forms.ModelForm):
    class Meta:
        model = Pet
        fields = "__all__"
