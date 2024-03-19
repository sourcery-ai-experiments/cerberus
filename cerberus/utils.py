# Standard Library
from datetime import date, datetime

# Django
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
