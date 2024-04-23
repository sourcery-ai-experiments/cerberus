# Standard Library
from typing import Self

# Django
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy

# Third Party
from vanilla import CreateView, DetailView, ListView

# Locals
from ..filters import CustomerFilter
from ..forms import ContactForm, CustomerForm, UninvoicedChargesForm
from ..models import Contact, Customer
from .crud_views import Actions, CRUDViews, Crumb, extra_view


class CustomerDetail(DetailView):
    lookup_field = "sqid"

    def get_queryset(self):
        return Customer.objects.with_pets()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["uninvoiced_charge_form"] = UninvoicedChargesForm(customer=self.object)
        context["uninvoiced_charges"] = self.object.charges.filter(invoice=None)

        return context


class CustomerList(ListView):
    def get_queryset(self):
        if self.model is not None:
            return self.model._default_manager.with_counts().with_pets()
        return super().get_queryset()


class CustomerCRUD(CRUDViews):
    model = Customer
    form_class = CustomerForm
    filter_class = CustomerFilter
    sortable_fields = ["name"]
    url_lookup: str = "<sqid>"
    url_parts: dict[Actions, str] = {
        Actions.CREATE: "create",
        Actions.DETAIL: f"{url_lookup}",
        Actions.UPDATE: f"{url_lookup}/edit",
        Actions.DELETE: f"{url_lookup}/delete",
        Actions.LIST: "",
    }

    @classmethod
    def get_view_class(cls, action: Actions):
        if action == Actions.DETAIL:
            return CustomerDetail
        if action == Actions.LIST:
            return CustomerList
        return super().get_view_class(action)

    @extra_view(detail=True)
    def uninvoiced_charges(self: Self, request: HttpRequest, pk: int) -> HttpResponse:
        customer = get_object_or_404(Customer, pk=pk)
        form = UninvoicedChargesForm(customer=customer)

        return render(
            request,
            "cerberus/customer_charges.html",
            {
                "form": form,
                "customer": customer,
                "breadcrumbs": self.get_breadcrumbs(customer)
                + [
                    Crumb("Uninvoiced Charges", reverse_lazy("customer_uninvoiced_charges", kwargs={"pk": customer.pk}))
                ],
            },
        )


class ContactCreateView(CreateView):
    model = Contact
    form_class = ContactForm

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        customer = get_object_or_404(Customer, pk=kwargs["pk"])
        context = self.get_context_data(form=form, customer=customer)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        customer = get_object_or_404(Customer, pk=kwargs["pk"])
        form = self.get_form(data=request.POST, files=request.FILES)
        if form.is_valid():
            self.object = form.save(commit=False)
            self.object.customer = customer
            self.object.save()
            return HttpResponseRedirect(self.get_success_url())

        context = self.get_context_data(form=form, customer=customer)
        return self.render_to_response(context)
