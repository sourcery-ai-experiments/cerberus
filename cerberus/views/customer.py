# Standard Library
from typing import Self

# Django
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy

# Third Party
from vanilla import DetailView, ListView

# Locals
from ..filters import CustomerFilter
from ..forms import CustomerForm, UninvoicedChargesForm
from ..models import Customer
from .crud_views import Actions, CRUDViews, Crumb, extra_view


class CustomerDetail(DetailView):
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
