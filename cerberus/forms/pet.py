# Django
from django import forms

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
        widgets = {"tags": TagsWidget()}
        help_texts = {"tags": None}
