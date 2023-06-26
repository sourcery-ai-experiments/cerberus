# Django
from django import forms

# Locals
from .models import Customer


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = "__all__"
        # fields = ["first_name","last_name","other_names","invoice_address","invoice_email"]
