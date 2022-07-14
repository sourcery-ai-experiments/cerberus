# Standard Library

# Django
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render  # noqa
from django.views.generic import DetailView, ListView

# Locals
from .models import Customer, Invoice, Pet, Vet


def InvoicePDF(request, pk):
    invoice = get_object_or_404(Invoice, id=pk)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{invoice.name}.pdf"'

    pisa_status = invoice.render_pdf(response)

    if pisa_status.err:
        return HttpResponse("We had some errors <pre>" + pisa_status.err + "</pre>")

    return response


class CustomerListView(ListView):
    model = Customer
    context_object_name = "customers"


class CustomerEditView(DetailView):
    model = Customer
    context_object_name = "customer"


class PetListView(ListView):
    model = Pet
    context_object_name = "pets"


class VetListView(ListView):
    model = Vet
    context_object_name = "vets"
