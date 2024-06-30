# Standard Library
import inspect
from collections.abc import Callable

# Django
from django.db.models import Model
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views import View

# Third Party
from django_htmx.http import HttpResponseClientRedirect


class TransitionView(View):
    model = Model
    field = str
    lookup_field: str = "pk"

    def get_valid_model(self, lookup_value, action: str):
        model = get_object_or_404(self.model, **{self.lookup_field: lookup_value})

        transitions = getattr(model, f"get_all_{self.field}_transitions")()
        available_transitions = getattr(model, f"get_all_{self.field}_transitions")()

        if action not in [t.name for t in transitions]:
            raise Http404(f"{action} is not a valid action on {self.model._meta.model_name}")

        if action not in [t.name for t in available_transitions]:
            raise Http404(f"{action} is not currently available on {self.model._meta.model_name}")

        return model

    def get(self, request, action: str, **kwargs):
        lookup_value = kwargs.get(self.lookup_field)
        model = self.get_valid_model(lookup_value, action)

        getattr(model, action)()
        redirect_url = getattr(model, "get_absolute_url", lambda: "/")()

        if request.htmx:
            return HttpResponseClientRedirect(redirect_url)
        return redirect(redirect_url)

    def post(self, request, action: str, **kwargs):
        lookup_value = kwargs.get(self.lookup_field)

        model = self.get_valid_model(lookup_value, action)

        action_function: Callable = getattr(model, action)

        args = {}
        for name, _ in inspect.signature(action_function).parameters.items():
            if name in request.POST:
                args[name] = request.POST[name]

        action_function(**args)
        redirect_url = getattr(model, "get_absolute_url", lambda: "/")()

        if request.htmx:
            return HttpResponseClientRedirect(redirect_url)
        return redirect(redirect_url)
