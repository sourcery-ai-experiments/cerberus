# Standard Library
from datetime import datetime, timedelta

# Django
from django import forms

# Locals
from ..models import Booking
from ..utils import minimize_whitespace
from ..widgets import CheckboxDataOptionAttr, CheckboxTable, SelectDataAttrField, SingleMoneyWidget


class BookingForm(forms.ModelForm):
    attributes = {
        "x-data": minimize_whitespace(
            """
            {
                cost: '',
                cost_per_additional: '',
                cost_changed: false,
                cost_per_additional_changed: false,
                customer: '',
                pets: [],
                start: '',
                end: '',
                length: 0,
                end_changed: false,
            }
"""
        ),
        "x-effect": minimize_whitespace(
            """
            if (length > 0 && start != '') {
                $nextTick(() => {
                    if (!end_changed) {
                        end = dateToString(addMinutes(start, length));
                        end_changed = false;
                    }
                });
            }
"""
        ),
    }

    class Meta:
        model = Booking
        fields = [
            "customer",
            "pets",
            "service",
            "cost",
            "cost_per_additional",
            "start",
            "end",
        ]
        widgets = {
            "customer": forms.Select(
                attrs={
                    "x-model.number.fill": "customer",
                    "@change": minimize_whitespace(
                        """
                        pets.length = 0;
                        $nextTick(() => {
                            $el.closest('form')
                                .querySelectorAll(`input[data-customer__id="${customer}"]`)
                                .forEach((el) => {
                                    pets.push(el.value);
                                });
                        });
"""
                    ),
                }
            ),
            "pets": CheckboxDataOptionAttr(
                "customer.id",
                attrs={
                    ":disabled": "!customer",
                    "x-model.number.fill": "pets",
                    "x-cloak": True,
                    ":class": "customer != $el.dataset.customer__id ? 'hidden' : 'visible'",
                },
            ),
            "service": SelectDataAttrField(
                ["cost.amount", "length_minutes", "cost_per_additional.amount"],
                attrs={
                    "@change": minimize_whitespace(
                        """
                        if (!cost_changed) {
                            $nextTick(() => {
                                const { dataset } = $event.target.options[$event.target.selectedIndex];
                                cost = (parseFloat(dataset.cost__amount) || 0.0).toFixed(2);
                                cost_per_additional = (parseFloat(dataset.cost_per_additional__amount) || 0.0).toFixed(2);
                            });
                            cost_changed = false;
                            cost_per_additional_changed = false;
                        }
                        $nextTick(() => length = $event.target.options[$event.target.selectedIndex].dataset.length_minutes);
"""
                    ),
                },
            ),
            "cost": SingleMoneyWidget(
                attrs={
                    "x-model.fill": "cost",
                    "@focus": "!cost_changed && $event.target.select()",
                    "@change": "cost_changed = $event.target.value !== ''",
                }
            ),
            "cost_per_additional": SingleMoneyWidget(
                attrs={
                    "x-model.fill": "cost_per_additional",
                    "@focus": "!cost_changed && $event.target.select()",
                    "@change": "cost_per_additional_changed = $event.target.value !== ''",
                }
            ),
            "start": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                    "step": 900,
                    "x-model.fill": "start",
                    "@change": "start = roundTime(start)",
                }
            ),
            "end": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                    "step": 900,
                    "x-model.fill": "end",
                    "@change": minimize_whitespace(
                        """
                        end_changed = $event.target.value !== '';
                        end = roundTime(end);
"""
                    ),
                }
            ),
        }


CompletableBookingTimeFrames = [
    ("day", "Day"),
    ("week", "Week"),
    ("month", "Month"),
    (None, "All"),
]


class CompletableBookingForm(forms.Form):
    bookings = forms.ModelMultipleChoiceField(
        queryset=Booking.objects.completable(),
        widget=CheckboxTable(
            [
                "pets.all",
                "customer",
                "service",
                "start",
            ],
            {"pets.all": "Pets"},
            "No completable bookings found.",
        ),
    )

    def __init__(self, *args, **kwargs):
        timeframe = kwargs.pop("timeframe", None)
        super().__init__(*args, **kwargs)
        if timeframe is not None:
            match timeframe:
                case "day":
                    delta = timedelta(days=0)
                case "week":
                    delta = timedelta(days=7)
                case "month":
                    delta = timedelta(days=30)
                case invalid:
                    raise ValueError(f"Invalid timeframe: {invalid}")
            self.fields["bookings"].queryset = self.fields["bookings"].queryset.filter(
                start__gte=datetime.now() - delta
            )
