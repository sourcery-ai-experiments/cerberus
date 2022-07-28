# Standard Library
from enum import Enum
from typing import TypeVar

# Django
from django.db import models


def choice_length(choices: type[models.TextChoices]) -> int:
    return max(len(choice[0]) for choice in choices.choices if choice[0] is not None)


T = TypeVar("T", bound="ChoicesEnum")


class ChoicesEnum(Enum):
    @classmethod
    def choices(cls: type[T]) -> list[tuple[str, str]]:
        return [(str(e.value), str(e.value)) for e in list(cls)]
