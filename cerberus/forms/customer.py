# Django
from django import forms

# Locals
from ..models import Customer
from ..widgets import TagsWidget


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
        widgets = {"tags": TagsWidget()}
        help_texts = {"tags": None}
