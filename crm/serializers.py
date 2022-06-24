# Standard Library
from enum import Enum

# Django
from django.core.exceptions import ObjectDoesNotExist

# Third Party
from rest_framework import serializers
from taggit.models import Tag
from taggit.serializers import TaggitSerializer, TagListSerializerField

# Locals
from .models import Address, Booking, BookingSlot, Charge, Contact, Customer, Pet, Service, Vet

default_read_only = [
    "id",
    "created",
    "last_updated",
]


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


class ContactSerializer(serializers.ModelSerializer, NestedObjectSerializer):
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


class ChargeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = Charge
        fields = "__all__"
        read_only_fields = default_read_only


class BookingSlotSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = BookingSlot
        fields = "__all__"
        read_only_fields = default_read_only


class ServiceSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = Service
        fields = "__all__"
        read_only_fields = default_read_only


class BookingSerializer(serializers.ModelSerializer):
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


class AddressSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = Address
        fields = "__all__"
        read_only_fields = default_read_only


class PetSerializer(TaggitSerializer, serializers.ModelSerializer, NestedObjectSerializer):
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


class VetSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    pets = PetSerializer(many=True, read_only=True)

    class Meta:
        model = Vet
        fields = "__all__"
        read_only_fields = default_read_only


class CustomerSerializer(TaggitSerializer, serializers.ModelSerializer, NestedObjectSerializer):
    id = serializers.ReadOnlyField()
    pets = PetSerializer(many=True, read_only=True, source="active_pets")
    addresses = AddressSerializer(many=True, read_only=True)
    contacts = ContactSerializer(many=True, read_only=True)
    charges = ChargeSerializer(many=True, read_only=True)
    bookings = BookingSerializer(many=True, read_only=True)
    vet_id = serializers.IntegerField(write_only=True)
    tags = TagListSerializerField()

    class Meta:
        model = Customer
        fields = "__all__"
        read_only_fields = default_read_only
        depth = 1

    def validate(self, attrs):
        attrs = self.fixNestedObject(attrs, "vet", Vet, False)

        return super().validate(attrs)


class TagSerializer(serializers.BaseSerializer):
    def to_representation(self, obj: Tag) -> str:
        return obj.name
