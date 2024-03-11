# Standard Library

# Standard Library
from typing import Self

# Django
from django.forms import modelformset_factory
from django.http import HttpRequest, HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy

# Third Party
from vanilla import CreateView, UpdateView

# Locals
from ..filters import InvoiceFilter
from ..forms import ChargeForm, InvoiceForm
from ..models import Charge, Invoice
from .crud_views import Actions, CRUDViews, extra_view


class InvoiceUpdateView(UpdateView):
    def get_success_url(self):
        return reverse_lazy("invoice_detail", kwargs={"pk": self.object.id})

    def get_formset(self):
        return modelformset_factory(Charge, form=ChargeForm, extra=1)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        formset = self.get_formset()
        context["formset"] = formset(queryset=context["object"].charges.all())

        return context

    def post(self, request, *args, **kwargs):
        formset = self.get_formset()(data=request.POST, files=request.FILES)
        if formset.is_valid():
            formset.save()
            return super().post(request, *args, **kwargs)

        form = self.get_form(
            data=request.POST,
            files=request.FILES,
            instance=self.object,
        )
        return self.form_invalid(form)


class InvoiceCreateView(CreateView):
    def get(self, request, *args, **kwargs):
        form = self.get_form(initial={k: str(v) for k, v in request.GET.items()})
        context = self.get_context_data(form=form)
        return self.render_to_response(context)


class InvoiceCRUD(CRUDViews):
    model = Invoice
    form_class = InvoiceForm
    filter_class = InvoiceFilter
    sortable_fields = ["id", "customer", "total"]

    @classmethod
    def get_view_class(cls, action: Actions):
        match action:
            case Actions.UPDATE:
                return InvoiceUpdateView
            case Actions.CREATE:
                return InvoiceCreateView
            case _:
                return super().get_view_class(action)

    @extra_view(detail=True, methods=["get", "post"])
    def email(self: Self, request: HttpRequest, pk: int) -> HttpResponse:
        invoice = get_object_or_404(Invoice, pk=pk)
        if request.method != "POST":
            return render(request, "cerberus/invoice_email_confirm.html", {"object": invoice, "invoice": invoice})
        try:
            invoice.resend_email()
        except AssertionError as e:
            return HttpResponseNotAllowed(f"Email not sent: {e}")

        return render(request, "cerberus/invoice_email_sent.html", {"object": invoice, "invoice": invoice})

    @extra_view(detail=True, methods=["get"], url_name="invoice_pdf")
    def download(self: Self, request: HttpRequest, pk: int) -> HttpResponse:
        invoice: Invoice = get_object_or_404(Invoice, pk=pk)

        return invoice.get_pdf_response()
