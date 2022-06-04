# Django
from django.db import models
from django.test import TestCase

# Locals
from ..utils import ChoicesEnum, choice_length


class test_choice_length(TestCase):
    def test_max_length(self):
        class testLength(models.TextChoices):
            ONE = "one", "One"
            TWO = "two", "Two"
            THREE = "three", "Three"
            __empty__ = "empty", "Empty"

        self.assertEqual(choice_length(testLength), 5)


class test_choices_enum(TestCase):
    def test_list(self):
        class choicesList(ChoicesEnum):
            ONE = "one"
            TWO = "two"
            THREE = "three"

        self.assertEqual(
            choicesList.choices(),
            [
                ("one", "one"),
                ("two", "two"),
                ("three", "three"),
            ],
        )
