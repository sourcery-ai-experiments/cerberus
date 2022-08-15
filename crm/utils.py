# Standard Library

# Django
from django.db import models


def choice_length(choices: type[models.TextChoices]) -> int:
    return max(len(choice[0]) for choice in choices.choices if choice[0] is not None)
