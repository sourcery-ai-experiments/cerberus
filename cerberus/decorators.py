# Standard Library
import functools

# Django
from django.db import transaction
from django.db.models import Model


def save_after(func):
    @functools.wraps(func)
    def wrapper_save(model: Model, *args, **kwargs):
        with transaction.atomic():
            return_val = func(model, *args, **kwargs)
            model.save()

        return return_val

    return wrapper_save
