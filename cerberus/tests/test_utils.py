# Django
from django.db import models

# Locals
from ..utils import choice_length


def test_max_length():
    class TestLength(models.TextChoices):
        ONE = "one", "One"
        TWO = "two", "Two"
        THREE = "three", "Three"
        __empty__ = "empty", "Empty"

    assert choice_length(TestLength) == 5
