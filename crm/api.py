# Standard Library
import contextlib

# Django
from django.db import transaction

# Third Party
from django_filters import rest_framework as filters
from django_fsm import TransitionNotAllowed
from rest_framework import filters as drf_filters
from rest_framework import mixins, permissions, routers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from taggit.models import Tag

# Locals
from .models import Address, Booking, BookingSlot, Charge, Contact, Customer, Pet, Service, Vet
from .serializers import (
    AddressSerializer,
    BookingSerializer,
    BookingSlotSerializer,
    ChargeSerializer,
    ContactSerializer,
    CustomerSerializer,
    PetSerializer,
    ServiceSerializer,
    TagSerializer,
    VetSerializer,
)


class FilterDefaults(filters.FilterSet):
    default_filters = {}

    def __init__(self, data=None, *args, **kwargs):
        if data is not None:
            data = data.copy()
            for key, value in self.default_filters.items():
                if key not in data:
                    data[key] = value

        super().__init__(data, *args, **kwargs)


class PetFilter(FilterDefaults):
    default_filters = {
        "active": True,
    }

    class Meta:
        model = Pet
        fields = ["active"]


class CustomerFilter(FilterDefaults):
    default_filters = {
        "active": True,
    }

    class Meta:
        model = Customer
        fields = ["active"]


class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]


class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def change_state(self, action: str) -> Response:
        booking = self.get_object()
        status = 400

        with transaction.atomic(), contextlib.suppress(TransitionNotAllowed):
            getattr(booking, action)()
            booking.save()
            status = 200

        serializer = self.get_serializer(booking)

        return Response({"booking": serializer.data, "status": status}, status=status)

    @action(detail=True, methods=["put"])
    def process(self, request, pk=None):
        return self.change_state("process")

    @action(detail=True, methods=["put"])
    def confirm(self, request, pk=None):
        return self.change_state("confirm")

    @action(detail=True, methods=["put"])
    def cancel(self, request, pk=None):
        return self.change_state("cancel")

    @action(detail=True, methods=["put"])
    def reopen(self, request, pk=None):
        return self.change_state("reopen")

    @action(detail=True, methods=["put"])
    def complete(self, request, pk=None):
        return self.change_state("complete")


class BookingSlotViewSet(viewsets.ModelViewSet):
    queryset = BookingSlot.objects.all()
    serializer_class = BookingSlotSerializer
    permission_classes = [permissions.IsAuthenticated]


class ChargeViewSet(viewsets.ModelViewSet):
    queryset = Charge.objects.all()
    serializer_class = ChargeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def change_state(self, action: str) -> Response:
        charge = self.get_object()
        status = 400

        with transaction.atomic(), contextlib.suppress(TransitionNotAllowed):
            getattr(charge, action)()
            charge.save()
            status = 200

        serializer = self.get_serializer(charge)

        return Response({"charge": serializer.data, "status": status}, status=status)

    @action(detail=True, methods=["put"])
    def pay(self, request, pk=None):
        return self.change_state("pay")

    @action(detail=True, methods=["put"])
    def void(self, request, pk=None):
        return self.change_state("void")

    @action(detail=True, methods=["put"])
    def refund(self, request, pk=None):
        return self.change_state("refund")


class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = CustomerFilter


class PetViewSet(viewsets.ModelViewSet):
    queryset = Pet.objects.all()
    serializer_class = PetSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = PetFilter


class VetViewSet(viewsets.ModelViewSet):
    queryset = Vet.objects.all()
    serializer_class = VetSerializer
    permission_classes = [permissions.IsAuthenticated]


class TagViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    filter_backends = [drf_filters.SearchFilter]
    search_fields = ["name"]
    pagination_class = None


router = routers.DefaultRouter()
router.register(r"Address", AddressViewSet)
router.register(r"Service", ServiceViewSet)
router.register(r"Booking", BookingViewSet)
router.register(r"BookingSlot", BookingSlotViewSet)
router.register(r"Charge", ChargeViewSet)
router.register(r"Contact", ContactViewSet)
router.register(r"Customer", CustomerViewSet)
router.register(r"Pet", PetViewSet)
router.register(r"Vet", VetViewSet)
router.register(r"Tag", TagViewSet)
