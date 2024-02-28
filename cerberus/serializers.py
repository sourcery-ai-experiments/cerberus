# Standard Library
from enum import Enum

# Django
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

# Third Party
from django_fsm_log.models import StateLog
from djmoney.contrib.django_rest_framework import MoneyField
from rest_framework import serializers
from taggit.serializers import TaggitSerializer, TagListSerializerField

# Locals
from .models import Address, Booking, BookingSlot, Charge, Contact, Customer, Invoice, Pet, Service, UserSettings, Vet

default_read_only = [
    "id",
    "created",
    "last_updated",
]


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed."""

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop("fields", None)
        exclude = kwargs.pop("exclude", None)

        super().__init__(*args, **kwargs)

        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

        if exclude is not None:
            exclude = set(exclude)
            existing = set(self.fields)
            for field_name in existing.intersection(exclude):
                self.fields.pop(field_name)


class EnumSerializer(serializers.Serializer):
    def to_representation(self, obj: Enum) -> str:
        return obj.value


class NestedObjectSerializer:
    def fix_nested_object(self, attrs, name, model, required=True, id_name=None):
        id_name = id_name if id_name is not None else f"{name}_id"

        if not required:
            attrs[name] = None

        try:
            if attrs[id_name] > 0:
                attrs[name] = model.objects.get(id=attrs[id_name])
        except (AttributeError, KeyError):
            pass
        except ObjectDoesNotExist as e:
            raise serializers.ValidationError({id_name: [str(e)]}) from e

        try:
            del attrs[id_name]
        except (AttributeError, KeyError):
            pass

        return attrs


class StatusLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = StateLog
        fields = [
            "timestamp",
            "source_state",
            "state",
            "transition",
            "description",
            "by",
        ]
        read_only = True

    def get_fields(self, *args, **kwargs):
        fields = super().get_fields(*args, **kwargs)
        for field in fields:
            fields[field].read_only = True
        return fields


class ContactSerializer(DynamicFieldsModelSerializer, NestedObjectSerializer):
    id = serializers.ReadOnlyField()
    type = EnumSerializer(read_only=True)
    customer_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Contact
        fields = ["id", "type", "name", "details", "customer_id"]
        read_only_fields = default_read_only

    def validate(self, attrs):
        attrs = self.fix_nested_object(attrs, "customer", Customer)

        return super().validate(attrs)


class ChargeSerializer(DynamicFieldsModelSerializer, NestedObjectSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Charge
        exclude = ("polymorphic_ctype",)
        read_only_fields = ["created", "last_updated"]


class BookingSlotSerializer(DynamicFieldsModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = BookingSlot
        fields = "__all__"
        read_only_fields = default_read_only


class ServiceSerializer(DynamicFieldsModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = Service
        fields = "__all__"
        read_only_fields = default_read_only


class BookingSerializer(DynamicFieldsModelSerializer):
    id = serializers.ReadOnlyField()
    service = ServiceSerializer()

    class Meta:
        model = Booking
        fields = [
            "id",
            "name",
            "cost",
            "start",
            "end",
            "created",
            "last_updated",
            "state",
            "pet",
            "service",
            "booking_slot",
            "can_move",
            "available_state_transitions",
        ]
        read_only_fields = default_read_only + [
            "state",
        ]


class BookingMoveSerializer(serializers.Serializer):
    to = serializers.DateTimeField()


class BookingSlotMoveSerializer(serializers.Serializer):
    start = serializers.DateTimeField()


class AddressSerializer(DynamicFieldsModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = Address
        fields = "__all__"
        read_only_fields = default_read_only


class CustomerDetailsOnlySerializer(DynamicFieldsModelSerializer):
    name = serializers.CharField(read_only=True)

    class Meta:
        model = Customer
        fields = "__all__"


class PetDropDownSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    customer = serializers.CharField(read_only=True)


class PetSerializer(TaggitSerializer, DynamicFieldsModelSerializer, NestedObjectSerializer):
    id = serializers.ReadOnlyField()
    tags = TagListSerializerField()
    customer_id = serializers.IntegerField(write_only=True)
    vet_id = serializers.IntegerField(write_only=True)
    customer = CustomerDetailsOnlySerializer(read_only=True)

    class Meta:
        model = Pet
        fields = "__all__"
        read_only_fields = default_read_only
        depth = 1

    def validate(self, attrs):
        attrs = self.fix_nested_object(attrs, "customer", Customer)
        attrs = self.fix_nested_object(attrs, "vet", Vet, False)

        return super().validate(attrs)


class VetSerializer(DynamicFieldsModelSerializer):
    id = serializers.ReadOnlyField()
    pets = PetSerializer(many=True, read_only=True, exclude=("vet", "customer"))

    class Meta:
        model = Vet
        fields = "__all__"
        read_only_fields = default_read_only


class CustomerDropDownSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)


class CustomerSerializer(TaggitSerializer, DynamicFieldsModelSerializer, NestedObjectSerializer):
    id = serializers.ReadOnlyField()
    name = serializers.CharField(read_only=True)
    pets = PetSerializer(many=True, read_only=True, source="active_pets", exclude=("customer",))
    addresses = AddressSerializer(many=True, read_only=True, exclude=("customer",))
    contacts = ContactSerializer(many=True, read_only=True, exclude=("customer",))
    bookings = BookingSerializer(many=True, read_only=True)
    vet = VetSerializer(many=False, read_only=True, exclude=("customers", "pets"))
    vet_id = serializers.IntegerField(write_only=True)
    tags = TagListSerializerField(required=False)
    invoiced_unpaid = MoneyField(max_digits=10, decimal_places=2, read_only=True)
    unpaid_count = serializers.IntegerField(read_only=True)
    overdue_count = serializers.IntegerField(read_only=True)
    issues = serializers.ListSerializer(child=serializers.CharField(read_only=True), read_only=True)

    class Meta:
        model = Customer
        fields = "__all__"
        read_only_fields = default_read_only
        depth = 0

    def validate(self, attrs):
        attrs = self.fix_nested_object(attrs, "vet", Vet, False)

        return super().validate(attrs)


class InvoiceSerializer(DynamicFieldsModelSerializer, NestedObjectSerializer):
    name = serializers.CharField(read_only=True)
    customer = CustomerSerializer(read_only=True, fields=("id", "name", "invoice_address"))
    charges = ChargeSerializer(many=True, exclude=("invoice",))
    customer_id = serializers.IntegerField(write_only=True)
    overdue = serializers.BooleanField(read_only=True)
    subtotal = MoneyField(max_digits=10, decimal_places=2, read_only=True)
    total = MoneyField(max_digits=10, decimal_places=2, read_only=True)
    available_state_transitions = serializers.ListField(read_only=True, child=serializers.CharField(read_only=True))
    can_edit = serializers.BooleanField(read_only=True)
    state_log = StatusLogSerializer(read_only=True, many=True)

    class Meta:
        model = Invoice
        fields = "__all__"
        read_only_fields = default_read_only

    def validate(self, attrs):
        if self.instance and not getattr(self.instance, "can_edit", True):
            raise serializers.ValidationError("Only draft invoices can be edited")

        attrs = self.fix_nested_object(attrs, "customer", Customer)
        return super().validate(attrs)

    @transaction.atomic
    def update(self, invoice: Invoice, validated_data):
        charges_data = validated_data.pop("charges") or []

        charges = []
        for charge_data in charges_data:
            charge_data.invoice = invoice
            charge_data.customer = invoice.customer

            try:
                charge_id = charge_data.pop("id")
                charge = Charge.objects.get(id=charge_id)
            except KeyError:
                charge = None

            charge_serializer: ChargeSerializer = ChargeSerializer(data=charge_data, instance=charge)
            if charge_serializer.is_valid():
                charge = charge_serializer.save()
                charge.invoice = invoice
                charge.save()
                charges.append(charge)

        ids = list(map(lambda c: c.id, charges))

        for charge in invoice.charges.all():
            if charge.id not in ids:
                charge.delete()

        return super().update(invoice, validated_data)

    @transaction.atomic
    def create(self, validated_data):
        charges_data = validated_data["charges"] or []
        del validated_data["charges"]
        invoice = super().create(validated_data)

        charges = []
        for charge_data in charges_data:
            charge_data.invoice = invoice
            charge_data.customer = invoice.customer

            charge_serializer: ChargeSerializer = ChargeSerializer(data=charge_data)
            if charge_serializer.is_valid():
                charge = charge_serializer.save()
                charge.invoice = invoice
                charge.save()
                charges.append(charge)

        return invoice


class InvoiceSendSerializer(serializers.Serializer):
    to = serializers.EmailField(default="")
    send_email = serializers.BooleanField(default=True)
    send_notes = serializers.CharField(default="")


class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = "__all__"

        extra_kwargs = {"user": {"read_only": True}}
