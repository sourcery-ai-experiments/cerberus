# Django
from django.db import models
from django.test import TestCase

# Locals
from ..utils import choice_length


class test_choice_length(TestCase):
    def test_max_length(self):
        class testLength(models.TextChoices):
            ONE = "one", "One"
            TWO = "two", "Two"
            THREE = "three", "Three"

        self.assertEqual(choice_length(testLength), 5)
