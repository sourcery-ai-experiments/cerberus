# Standard Library
import random

# Django
from django.test import TestCase

# Third Party
from model_bakery import baker
from moneyed import Money

# Locals
from ..models import Customer

baker.generators.add("djmoney.models.fields.MoneyField", lambda: Money(random.uniform(1.0, 100.0), "GBP"))


class InvoiceTests(TestCase):
    def setUp(self) -> None:
        self.customer: Customer = baker.make(Customer, invoice_email="test@example.com")

    def test_full_name(self):
        self.assertEqual(self.customer.name, f"{self.customer.first_name} {self.customer.last_name}")
