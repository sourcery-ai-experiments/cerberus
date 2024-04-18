# Django
from django import forms

# Locals
from ..models import Contact


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = [
            "name",
            "details",
        ]
        widgets = {
            "details": forms.TextInput(
                attrs={
                    "x-data": "",
                    "x-mask:dynamic": "$input.startsWith('0') ? '99999 999 999' : false",
                }
            ),
        }
