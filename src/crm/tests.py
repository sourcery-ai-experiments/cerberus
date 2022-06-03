# Django
from django.test import TestCase

# Locals
from .utils import max_length


class test_choice_length(TestCase):
    def test_max_length(self):
        class testLength:
            ONE = "one", "One"
            TWO = "two", "Two"
            THREE = "three", "Three"

        self.assertEqual(max_length(testLength), 3)
