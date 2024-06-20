# Django
from django import forms

# Locals
from ..models import Charge
from ..widgets import SingleMoneyWidget


class ChargeForm(forms.ModelForm):
    class Meta:
        model = Charge
        fields = ["name", "line", "quantity"]
        widgets = {
            "line": SingleMoneyWidget(attrs={"x-model.fill": "line", "min": "0"}),
            "quantity": forms.NumberInput(attrs={"x-model.number.fill": "quantity"}),
        }
