# Standard Library
import functools
import re
from datetime import date, datetime
from functools import lru_cache

# Django
from django.conf import settings
from django.db import models
from django.utils.timezone import make_aware as django_make_aware


def choice_length(choices: type[models.TextChoices]) -> int:
    return max(len(choice[0]) for choice in choices.choices if choice[0] is not None)


def make_aware(value: date, timezone=None):
    if not isinstance(value, datetime):
        value = datetime(value.year, value.month, value.day)

    try:
        return django_make_aware(value, timezone)
    except ValueError:
        return value


@lru_cache(maxsize=128)
def minimize_whitespace(value: str) -> str:
    if settings.DEBUG:
        return value
    return re.sub(r"(^\s+|[\n\r]+)", "", value, flags=re.MULTILINE).strip()


def rgetattr(obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)

    return functools.reduce(_getattr, [obj] + attr.split("."))
