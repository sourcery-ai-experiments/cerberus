# Django
from django import forms

# Locals
from .models import Booking, Charge, Customer, Invoice, Pet, Service, Vet
from .utils import minimize_whitespace
from .widgets import CheckboxDataOptionAttr, CheckboxTable, SelectDataAttrField, SingleMoneyWidget


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
        widgets = {"tags": forms.TextInput()}


class PetForm(forms.ModelForm):
    class Meta:
        model = Pet
        fields = [
            "name",
            "dob",
            "active",
            "social_media_concent",
            "sex",
            "description",
            "neutered",
            "medical_conditions",
            "treatment_limit",
            "allergies",
            "tags",
            "customer",
            "vet",
        ]


class VetForm(forms.ModelForm):
    class Meta:
        model = Vet
        fields = [
            "name",
            "phone",
            "details",
        ]


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
                                cost = dataset.cost__amount;
                                cost_per_additional = dataset.cost_per_additional__amount;
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


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            "details",
            "due",
            "adjustment",
            "customer_name",
            "sent_to",
            "invoice_address",
            "send_notes",
        ]
        widgets = {
            "adjustment": SingleMoneyWidget(),
            "due": forms.DateInput(attrs={"type": "date"}),
        }


class ChargeForm(forms.ModelForm):
    class Meta:
        model = Charge
        fields = ["name", "line", "quantity"]
        widgets = {
            "line": SingleMoneyWidget(attrs={"x-model.fill": "line", "min": "0"}),
            "quantity": forms.NumberInput(attrs={"x-model.number.fill": "quantity"}),
        }


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = [
            "name",
            "length",
            "booked_length",
            "cost",
            "cost_per_additional",
            "max_pet",
            "max_customer",
            "display_colour",
        ]
        widgets = {
            "cost": SingleMoneyWidget(),
            "cost_per_additional": SingleMoneyWidget(),
            "display_colour": forms.TextInput(attrs={"type": "color"}),
        }


class UninvoicedChargesForm(forms.Form):
    customer = forms.ModelChoiceField(queryset=Customer.objects.all(), widget=forms.HiddenInput, required=True)
    charges = forms.ModelMultipleChoiceField(
        queryset=Charge.objects.none(),
        widget=CheckboxTable(["name", "amount", "booking.date"]),
    )

    def __init__(self, *args, **kwargs):
        customer = kwargs.pop("customer", None)
        super().__init__(*args, **kwargs)

        if self.is_bound and (customer_id := self.data.get("customer", None)):
            self.set_customer(customer_id)
        elif isinstance(customer, Customer):
            self.set_customer(customer.pk)
        elif isinstance(customer, int):
            self.set_customer(customer)
        else:
            raise ValueError("No customer provided")

    def set_customer(self, customer_id: int | None) -> None:
        self.fields["customer"].initial = customer_id
        self.fields["charges"].queryset = Charge.objects.filter(customer_id=customer_id, invoice__isnull=True)


class InvoiceSendForm(forms.Form):
    attributes = {"x-data": minimize_whitespace("""{ send: true }""")}

    send_email = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={"x-model.boolean.fill": "send"}))
    to = forms.EmailField(required=True, widget=forms.EmailInput(attrs={":class": "{ 'display-none': ! send }"}))
    send_notes = forms.CharField(required=False, widget=forms.Textarea(attrs={":class": "{ 'display-none': ! send }"}))
