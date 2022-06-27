# Django
from django.test import TestCase

# Third Party
from model_bakery import baker

# Locals
from ..models import Charge, Customer, Invoice


class InvoiceTests(TestCase):
    def setUp(self) -> None:
        self.customer: Customer = baker.make(Customer)

    def test_change_charges(self):
        invoice = Invoice.objects.create(name="INV-001", customer=self.customer)
        invoice.save()

        charge = Charge.objects.create(name="test charge 1", customer=self.customer, cost=12.00, invoice=invoice)
        charge.save()

        invoice: Invoice = Invoice.objects.get(name="INV-001")
        self.assertIn(charge, invoice.charges.all())

        invoice.send()
        self.assertEqual(invoice.state, Invoice.States.UNPAID.value)

        invoice.pay()
        self.assertEqual(invoice.state, Invoice.States.PAID.value)

        self.assertTrue(all([c.state == Charge.States.PAID.value for c in invoice.charges.all()]))
