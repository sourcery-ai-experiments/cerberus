# Django
from django import forms
from django.forms import TextInput

# Locals
from ..models import Pet
from ..widgets import TagsWidget


class PetForm(forms.ModelForm):
    class Meta:
        model = Pet
        fields = [
            "name",
            "dob",
            "description",
            "sex",
            "neutered",
            "social_media_concent",
            "vet",
            "treatment_limit",
            "medical_conditions",
            "allergies",
            "tags",
        ]
        widgets = {
            "tags": TagsWidget(),
            "treatment_limit": TextInput(
                attrs={
                    "x-mask:dynamic": "$money($input)",
                    "x-data": "",
                    "@focus": "$el.value == 0 && $el.select()",
                }
            ),
        }
        help_texts = {"tags": None}
