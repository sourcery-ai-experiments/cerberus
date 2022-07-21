# Standard Library
import contextlib
from datetime import datetime, timedelta
from wsgiref.util import FileWrapper

# Django
from django.contrib.staticfiles import finders
from django.db import transaction
from django.http import HttpResponse

# Third Party
from django_filters import rest_framework as filters
from django_fsm import TransitionNotAllowed
from rest_framework import filters as drf_filters
from rest_framework import mixins, permissions, routers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from taggit.models import Tag

# Locals
from .filters import BookingFilter, CustomerFilter, InvoiceFilter, PetFilter
from .models import Address, Booking, BookingSlot, Charge, Contact, Customer, Invoice, Pet, Service, Vet
from .serializers import (
    AddressSerializer,
    BookingSerializer,
    BookingSlotSerializer,
    ChargeSerializer,
    ContactSerializer,
    CustomerDropDownSerializer,
    CustomerSerializer,
    InvoiceSerializer,
    PetSerializer,
    ServiceSerializer,
    TagSerializer,
    VetSerializer,
)

default_permissions = [permissions.IsAuthenticated]
default_permissions = []


class ActiveMixin:
    @action(detail=True, methods=["put"])
    def deactivate(self, request, pk=None):
        assert isinstance(self, viewsets.ModelViewSet), "Can only be used on ModelViewSet"
        object = self.get_object()
        object.active = False
        object.save()

        return Response({"status": "ok"})

    @action(detail=True, methods=["put"])
    def activate(self, request, pk=None):
        assert isinstance(self, viewsets.ModelViewSet), "Can only be used on ModelViewSet"
        object = self.get_object()
        object.active = True
        object.save()

        return Response({"status": "ok"})


class ChangeStateMixin:
    def change_state(self, action: str) -> Response:
        assert isinstance(self, viewsets.ModelViewSet), "Can only be used on ModelViewSet"
        item = self.get_object()
        status = 400

        with transaction.atomic(), contextlib.suppress(TransitionNotAllowed):
            getattr(item, action)()
            item.save()
            status = 200

        serializer = self.get_serializer(item)

        return Response({"item": serializer.data, "status": status}, status=status)


class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = default_permissions


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = default_permissions


class BookingViewSet(viewsets.ModelViewSet, ChangeStateMixin):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = default_permissions
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = BookingFilter

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
    permission_classes = default_permissions


class ChargeViewSet(viewsets.ModelViewSet):
    queryset = Charge.objects.all()
    serializer_class = ChargeSerializer
    permission_classes = default_permissions

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


class InvoiceViewSet(ChangeStateMixin, viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = default_permissions
    filter_backends = (filters.DjangoFilterBackend, drf_filters.OrderingFilter)
    filterset_class = InvoiceFilter

    ordering = "-created"
    ordering_fields = ("customer__name", "state", "due", "created", "total")

    @action(detail=True, methods=["put"])
    def send(self, request, pk=None):
        return self.change_state("send")

    @action(detail=True, methods=["put"])
    def pay(self, request, pk=None):
        return self.change_state("pay")

    @action(detail=True, methods=["put"])
    def void(self, request, pk=None):
        return self.change_state("void")

    @action(detail=True, methods=["get"])
    def resend(self, request, pk=None):
        item = self.get_object()
        item.send_email()
        return Response({"status": "ok"}, status=200)

    @action(detail=True, methods=["get"])
    def pdf(self, request, pk=None):
        invoice: Invoice = self.get_object()

        results = invoice.get_pdf()
        if results.err:
            raise Exception(results.err)

        return HttpResponse(
            content=results.dest.getvalue(),
            content_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{invoice.name}.pdf"'},
        )

    @action(detail=True, methods=["get"])
    def logo(self, request, pk=None):
        invoice = self.get_object()
        invoice.add_open()

        result = finders.find("img/logo-name.png")

        with open(f"{result}", "rb") as f:
            return HttpResponse(FileWrapper(f), content_type="image/png")

    @action(detail=False, methods=["get"])
    def overview(self, request):
        invoices = Invoice.objects

        recent = datetime.today() - timedelta(days=28)

        draft = invoices.filter(state=Invoice.States.DRAFT.value)
        unpaid = invoices.filter(state=Invoice.States.UNPAID.value)
        void = invoices.filter(state=Invoice.States.VOID.value, last_updated__gte=recent)
        paid = invoices.filter(state=Invoice.States.PAID.value, last_updated__gte=recent)

        return Response(
            {
                "draft": InvoiceSerializer(draft, many=True).data,
                "unpaid": InvoiceSerializer(unpaid, many=True).data,
                "void": InvoiceSerializer(void, many=True).data,
                "paid": InvoiceSerializer(paid, many=True).data,
            }
        )


class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = default_permissions


class CustomerViewSet(viewsets.ModelViewSet, ActiveMixin):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = default_permissions
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = CustomerFilter

    @action(detail=False, methods=["get"])
    def dropdown(self, request):
        serializer = CustomerDropDownSerializer(self.queryset, many=True)

        return Response({"results": serializer.data})

    @action(detail=True, methods=["get"])
    def accounts(self, request, pk=None):
        customer = self.get_object()
        invoices = Invoice.objects.filter(customer=customer)

        recent = datetime.today() - timedelta(days=28)

        draft = invoices.filter(state=Invoice.States.DRAFT.value)
        unpaid = invoices.filter(state=Invoice.States.UNPAID.value)
        void = invoices.filter(state=Invoice.States.VOID.value, last_updated__gte=recent)
        paid = invoices.filter(state=Invoice.States.PAID.value, last_updated__gte=recent)

        return Response(
            {
                "draft": InvoiceSerializer(draft, many=True).data,
                "unpaid": InvoiceSerializer(unpaid, many=True).data,
                "void": InvoiceSerializer(void, many=True).data,
                "paid": InvoiceSerializer(paid, many=True).data,
            }
        )


class PetViewSet(viewsets.ModelViewSet, ActiveMixin):
    queryset = Pet.objects.all()
    serializer_class = PetSerializer
    permission_classes = default_permissions
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = PetFilter


class VetViewSet(viewsets.ModelViewSet):
    queryset = Vet.objects.all()
    serializer_class = VetSerializer
    permission_classes = default_permissions


class TagViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    filter_backends = [drf_filters.SearchFilter]
    search_fields = ["name"]
    pagination_class = None


router = routers.DefaultRouter()
router.register(r"address", AddressViewSet)
router.register(r"service", ServiceViewSet)
router.register(r"booking", BookingViewSet)
router.register(r"bookingslot", BookingSlotViewSet)
router.register(r"charge", ChargeViewSet)
router.register(r"invoice", InvoiceViewSet)
router.register(r"contact", ContactViewSet)
router.register(r"customer", CustomerViewSet)
router.register(r"pet", PetViewSet)
router.register(r"vet", VetViewSet)
router.register(r"tag", TagViewSet)
