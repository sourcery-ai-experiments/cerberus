# Django
from django.db import models

# Internals
from cerberus.utils import choice_length


def test_max_length():
    class testLength(models.TextChoices):
        ONE = "one", "One"
        TWO = "two", "Two"
        THREE = "three", "Three"
        __empty__ = "empty", "Empty"

    assert choice_length(testLength) == 5
