# Standard Library
import functools

# Django
from django.db import transaction


def save_after(func):
    @functools.wraps(func)
    def wrapper_save(*args, **kwargs):
        with transaction.atomic():
            return_val = func(*args, **kwargs)
            args[0].save()

        return return_val

    return wrapper_save
