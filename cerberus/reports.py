# Django
from django.db.models import Count, F, Sum
from django.db.models.functions import ExtractWeek, ExtractYear
from django.urls import path

# Third Party
from rest_framework.response import Response
from rest_framework.views import APIView

# First Party
from cerberus.models import Invoice


class BaseInvoiceReport(APIView):
    def get_queryset(self):
        return Invoice.objects.all()


class InvoicePerWeek(BaseInvoiceReport):
    def get(self, request, format=None):
        invoices = (
            self.get_queryset()
            .filter(state__in=[Invoice.States.PAID, Invoice.States.UNPAID])
            .exclude(sent_on=None)
            .annotate(year=ExtractYear("sent_on"), week=ExtractWeek("sent_on"))
            .values("year", "week")
            .annotate(count=Count("id"))
            .annotate(
                subtotal=Sum(F("charges__line") * F("charges__quantity")),
                total=Sum("adjustment") + F("subtotal"),
            )
            .order_by("week")
        )

        return Response({"data": invoices})


urls = [path("invoice-per-week", InvoicePerWeek.as_view())]
