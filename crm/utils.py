# Standard Library
from enum import Enum

# Django
from django.db import models


def choice_length(choices: type[models.TextChoices]) -> int:
    return max(len(choice[0]) for choice in choices.choices if choice[0] is not None)


class ChoicesEnum(Enum):
    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        return [(e.value, e.value) for e in list(cls)]
