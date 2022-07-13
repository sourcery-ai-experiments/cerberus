# Standard Library
from enum import Enum

# Django
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

# Third Party
from djmoney.contrib.django_rest_framework import MoneyField
from rest_framework import serializers
from taggit.models import Tag
from taggit.serializers import TaggitSerializer, TagListSerializerField

# Locals
from .models import Address, Booking, BookingSlot, Charge, Contact, Customer, Invoice, Pet, Service, Vet

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
    def fixNestedObject(self, attrs, name, model, required=True, id_name=None):
        id_name = id_name if id_name is not None else f"{name}_id"

        if not required:
            attrs[name] = None

        try:
            if attrs[id_name] > 0:
                attrs[name] = model.objects.get(id=attrs[id_name])
        except AttributeError:
            pass
        except ObjectDoesNotExist as e:
            raise serializers.ValidationError({id_name: [str(e)]})

        del attrs[id_name]

        return attrs


class ContactSerializer(DynamicFieldsModelSerializer, NestedObjectSerializer):
    id = serializers.ReadOnlyField()
    type = EnumSerializer(read_only=True)
    customer_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Contact
        fields = ["id", "type", "name", "details", "customer_id"]
        read_only_fields = default_read_only

    def validate(self, attrs):
        attrs = self.fixNestedObject(attrs, "customer", Customer)

        return super().validate(attrs)


class ChargeSerializer(DynamicFieldsModelSerializer, NestedObjectSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = Charge
        exclude = ("polymorphic_ctype",)
        read_only_fields = default_read_only


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


class AddressSerializer(DynamicFieldsModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = Address
        fields = "__all__"
        read_only_fields = default_read_only


class PetSerializer(TaggitSerializer, DynamicFieldsModelSerializer, NestedObjectSerializer):
    id = serializers.ReadOnlyField()
    tags = TagListSerializerField()
    customer_id = serializers.IntegerField(write_only=True)
    vet_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Pet
        fields = "__all__"
        read_only_fields = default_read_only
        depth = 1

    def validate(self, attrs):
        attrs = self.fixNestedObject(attrs, "customer", Customer)
        attrs = self.fixNestedObject(attrs, "vet", Vet, False)

        return super().validate(attrs)


class VetSerializer(DynamicFieldsModelSerializer):
    id = serializers.ReadOnlyField()
    pets = PetSerializer(many=True, read_only=True, exclude=("vet",))

    class Meta:
        model = Vet
        fields = "__all__"
        read_only_fields = default_read_only


class CustomerDropDownSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)


class CustomerSerializer(TaggitSerializer, DynamicFieldsModelSerializer, NestedObjectSerializer):
    id = serializers.ReadOnlyField()
    pets = PetSerializer(many=True, read_only=True, source="active_pets", exclude=("customer",))
    addresses = AddressSerializer(many=True, read_only=True, exclude=("customer",))
    contacts = ContactSerializer(many=True, read_only=True, exclude=("customer",))
    charges = ChargeSerializer(many=True, read_only=True, exclude=("customer",))
    bookings = BookingSerializer(many=True, read_only=True)
    vet = VetSerializer(many=False, read_only=True, exclude=("customers",))
    vet_id = serializers.IntegerField(write_only=True)
    tags = TagListSerializerField()

    class Meta:
        model = Customer
        fields = "__all__"
        read_only_fields = default_read_only
        depth = 0

    def validate(self, attrs):
        attrs = self.fixNestedObject(attrs, "vet", Vet, False)

        return super().validate(attrs)


class TagSerializer(serializers.BaseSerializer):
    def to_representation(self, obj: Tag) -> str:
        return obj.name


class InvoiceSerializer(DynamicFieldsModelSerializer, NestedObjectSerializer):
    name = serializers.CharField(read_only=True)
    customer = CustomerSerializer(read_only=True, fields=("id", "name"))
    charges = ChargeSerializer(many=True, exclude=("invoice",))
    customer_id = serializers.IntegerField(write_only=True)
    overdue = serializers.BooleanField(read_only=True)
    total = MoneyField(max_digits=10, decimal_places=2, read_only=True)
    total_unpaid = MoneyField(max_digits=10, decimal_places=2, read_only=True)
    available_state_transitions = serializers.ListField(read_only=True, child=serializers.CharField(read_only=True))
    can_edit = serializers.BooleanField(read_only=True)

    class Meta:
        model = Invoice
        fields = "__all__"
        read_only_fields = default_read_only

    def validate(self, attrs):
        if self.instance and not getattr(self.instance, "can_edit", True):
            raise serializers.ValidationError("Only draft invoices can be edited")

        attrs = self.fixNestedObject(attrs, "customer", Customer)
        return super().validate(attrs)

    @transaction.atomic
    def create(self, validated_data):
        chargesData = validated_data["charges"] or []
        del validated_data["charges"]
        invoice = super().create(validated_data)

        charges = []
        for chargeData in chargesData:
            chargeData.invoice = invoice
            chargeData.customer = invoice.customer

            chargeSerializer = ChargeSerializer(data=chargeData)
            if chargeSerializer.is_valid():
                charge = chargeSerializer.save()
                charge.invoice = invoice
                charge.save()
                charges.append(charge)

        return invoice
