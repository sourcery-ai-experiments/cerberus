# Django
from django.db import models


def max_length(choices: models.TextChoices) -> int:
    return max(len(choice[0]) for choice in choices)
