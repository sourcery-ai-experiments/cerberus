# Standard Library

# Standard Library
from typing import Self

# Django
from django.db import transaction
from django.forms import modelformset_factory
from django.http import HttpRequest, HttpResponse, HttpResponseNotAllowed, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy

# Third Party
from django_htmx.http import HttpResponseClientRedirect
from vanilla import CreateView, UpdateView

# Locals
from ..filters import InvoiceFilter
from ..forms import ChargeForm, CustomerUninvoicedChargesForm, InvoiceForm, InvoiceSendForm
from ..models import Charge, Invoice
from .crud_views import Actions, CRUDViews, extra_view
from .transition_view import TransitionView


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
    sortable_fields = ["id", "customer", "total", "state"]

    @classmethod
    def url_lookup(cls) -> str:
        return "inv-<pint:pk>"

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

    @extra_view(detail=False, methods=["get", "post"], url_name="invoice_from_charges")
    def from_charges(self: Self, request: HttpRequest) -> HttpResponse:
        charge_form = CustomerUninvoicedChargesForm(request.POST)

        if charge_form.is_valid():
            with transaction.atomic():
                invoice = Invoice.from_customer(charge_form.cleaned_data["customer"])
                for charge in charge_form.cleaned_data["charges"]:
                    charge.invoice = invoice
                    charge.save()

            success_url = reverse_lazy("invoice_detail", kwargs={"pk": invoice.pk})
            if request.htmx:  # type: ignore
                return HttpResponseClientRedirect(success_url)
            return HttpResponseRedirect(success_url)

        return render(request, "cerberus/customer_charges.html", {"form": charge_form})

    @extra_view(detail=True, methods=["get", "post"], url_path="send", url_name="invoice_send")
    def send_form(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)
        inital = {"to": getattr(invoice.customer, "invoice_email", ""), "send_email": True}
        form = InvoiceSendForm(request.POST or inital)

        if request.POST and form.is_valid():
            invoice.send(form.cleaned_data["to"], form.cleaned_data["send_email"])
            return HttpResponseRedirect(reverse_lazy("invoice_detail", kwargs={"pk": invoice.pk}))

        return render(request, "cerberus/invoice_send_form.html", {"invoice": invoice, "form": form})


class InvoiceActionsView(TransitionView):
    model = Invoice
    field = "state"
