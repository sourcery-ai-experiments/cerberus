# Third Party
from vanilla import DetailView

# Locals
from ..filters import CustomerFilter
from ..forms import CustomerForm, UninvoicedChargesForm
from ..models import Customer
from .crud_views import Actions, CRUDViews


class CustomerDetail(DetailView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["uninvoiced_charge_form"] = UninvoicedChargesForm(customer=self.object)
        context["uninvoiced_charges"] = self.object.charges.filter(invoice=None)

        return context


class CustomerCRUD(CRUDViews):
    model = Customer
    form_class = CustomerForm
    filter_class = CustomerFilter
    sortable_fields = ["name"]

    @classmethod
    def get_view_class(cls, action: Actions):
        if action == Actions.DETAIL:
            return CustomerDetail
        return super().get_view_class(action)
