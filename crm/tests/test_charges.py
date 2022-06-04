# Django
from django.test import TestCase

# Locals
from ..models import Charge


class ChargeTests(TestCase):
    def test_str(self):
        charge = Charge(name="Test Charge", cost=1000)

        self.assertEqual(f"{charge}", "£10.00")

    def test_transitions(self):
        charge = Charge(name="Test Charge", cost=1000)
        transitions = list(charge.get_all_state_transitions())

        valid_transitions = [
            ("unpaid", "paid"),
            ("unpaid", "void"),
            ("paid", "refunded"),
        ]

        for t in transitions:
            self.assertIn((t.source, t.target), valid_transitions)

        self.assertEqual(len(valid_transitions), len(transitions))

    def test_paid(self):
        charge = Charge(name="Test Charge", cost=1000)
        charge.save()

        charge.pay()

        self.assertEqual(charge.state, Charge.States.PAID.value)
