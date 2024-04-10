# Standard Library
import inspect
from collections.abc import Callable

# Django
from django.db.models import Model
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views import View


class TransitionView(View):
    model = Model
    field = str

    def get_valid_model(self, pk: int, action: str):
        model = get_object_or_404(self.model, pk=pk)

        transitions = getattr(model, f"get_all_{self.field}_transitions")()
        available_transitions = getattr(model, f"get_all_{self.field}_transitions")()

        if action not in [t.name for t in transitions]:
            raise Http404(f"{action} is not a valid action on {self.model._meta.model_name}")

        if action not in [t.name for t in available_transitions]:
            raise Http404(f"{action} is not currently available on {self.model._meta.model_name}")

        return model

    def get(self, request, pk: int, action: str):
        model = self.get_valid_model(pk, action)

        getattr(model, action)()
        redirect_url = getattr(model, "get_absolute_url", lambda: "/")()

        return redirect(redirect_url)

    def post(self, request, pk: int, action: str):
        model = self.get_valid_model(pk, action)

        action_function: Callable = getattr(model, action)

        args = {}
        for name, _ in inspect.signature(action_function).parameters.items():
            if name in request.POST:
                args[name] = request.POST[name]

        action_function(**args)
        redirect_url = getattr(model, "get_absolute_url", lambda: "/")()

        return redirect(redirect_url)
