# Standard Library
import os

# Django
from django.conf import settings
from django.contrib.staticfiles import finders
from django.http import HttpResponse
from django.shortcuts import render  # noqa
from django.template.loader import get_template
from django.views.generic import DetailView, ListView

# Third Party
from xhtml2pdf import pisa

# Locals
from .models import Customer, Pet, Vet


def link_callback(uri, rel):
    """Convert HTML URIs to absolute system paths so xhtml2pdf can access those
    resources."""
    result = finders.find(uri)
    if result:
        if not isinstance(result, (list, tuple)):
            result = [result]
        result = list(os.path.realpath(path) for path in result)
        path = result[0]
    else:
        sUrl = settings.STATIC_URL  # Typically /static/
        sRoot = settings.STATIC_ROOT  # Typically /home/userX/project_static/
        mUrl = settings.MEDIA_URL  # Typically /media/
        mRoot = settings.MEDIA_ROOT  # Typically /home/userX/project_static/media/

        if uri.startswith(mUrl):
            path = os.path.join(mRoot, uri.replace(mUrl, ""))
        elif uri.startswith(sUrl):
            path = os.path.join(sRoot, uri.replace(sUrl, ""))
        else:
            return uri

    # make sure that file exists
    if not os.path.isfile(path):
        raise Exception(f"media URI must start with {sUrl} or {mUrl}")
    return path


def InvoicePDF(request, pk):
    template_path = "crm/invoice.html"
    context = {"invoice_ref": "Bob-008"}

    response = HttpResponse(content_type="application/pdf")
    # response['Content-Disposition'] = 'attachment; filename="report.pdf"'

    template = get_template(template_path)
    html = template.render(context)

    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    if pisa_status.err:
        return HttpResponse("We had some errors <pre>" + html + "</pre>")
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
