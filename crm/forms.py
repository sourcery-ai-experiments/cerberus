# Django
from django.forms import ModelForm

# Locals
from .models import Customer, Pet, Vet


class CustomerForm(ModelForm):
    class Meta:
        model = Customer
        fields = "__all__"


class PetForm(ModelForm):
    class Meta:
        model = Pet
        fields = "__all__"


class VetForm(ModelForm):
    class Meta:
        model = Vet
        fields = "__all__"
