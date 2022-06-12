# Standard Library
import functools
from enum import Enum

# Django
from django.db import models


def id_to_object(field: str, model: type[models.Model], dest: str | None = None):
    dest = dest if dest else f"{model.__name__}".lower()

    def decorator(func):
        @functools.wraps(func)
        def wrapper_id_to_object(*args, **kwargs):
            for arg in args:
                if isinstance(arg, dict):
                    if field in arg:
                        arg[dest] = model.objects.get(id=arg[field])
                        del arg[field]

            func(*args, **kwargs)
            return func(*args, **kwargs)

        return wrapper_id_to_object

    return decorator


def choice_length(choices: type[models.TextChoices]) -> int:
    return max(len(choice[0]) for choice in choices.choices if choice[0] is not None)


class ChoicesEnum(Enum):
    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        return [(str(e.value), str(e.value)) for e in list(cls)]
