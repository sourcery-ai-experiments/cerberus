# Django
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404

# Third Party
from vanilla import CreateView

# Locals
from ..filters import PetFilter
from ..forms import PetForm
from ..models import Customer, Pet
from .crud_views import Actions, CRUDViews


class PetCreateView(CreateView):
    model = Pet
    form_class = PetForm

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        customer = get_object_or_404(Pet, pk=kwargs["pk"])
        context = self.get_context_data(form=form, customer=customer)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        customer = get_object_or_404(Customer, pk=kwargs["pk"])
        form = self.get_form(data=request.POST, files=request.FILES)
        if form.is_valid():
            self.object = form.save(commit=False)
            self.object.customer = customer
            self.object.save()
            form.save_m2m()
            return HttpResponseRedirect(self.get_success_url())

        context = self.get_context_data(form=form, customer=customer)
        return self.render_to_response(context)


class PetCRUD(CRUDViews):
    model = Pet
    form_class = PetForm
    filter_class = PetFilter
    sortable_fields = ["name", "customer"]

    url_parts = {
        **CRUDViews.url_parts,
        **{Actions.CREATE: "create-for-customer/<int:pk>/"},
    }

    @classmethod
    def get_view_class(cls, action: Actions):
        if action == Actions.CREATE:
            return PetCreateView
        return super().get_view_class(action)
