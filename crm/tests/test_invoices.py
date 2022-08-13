# Django
from django.test import TestCase

# Third Party
from icecream import ic
from model_bakery import baker

# Locals
from ..models import Charge, Customer, Invoice


class InvoiceTests(TestCase):
    def setUp(self) -> None:
        self.customer: Customer = baker.make(Customer, invoice_email="test@example.com")

    def test_change_charges(self):
        base_invoice = Invoice.objects.create(customer=self.customer)
        base_invoice.save()
        invoice_pk = base_invoice.pk
        ic(self.customer.invoice_email)

        charge = Charge.objects.create(name="test charge 1", customer=self.customer, line=12.00, invoice=base_invoice)
        charge.save()

        invoice: Invoice = Invoice.objects.get(pk=invoice_pk)
        self.assertIn(charge, invoice.charges.all())

        invoice.send()
        self.assertEqual(invoice.state, Invoice.States.UNPAID.value)

        invoice.pay()
        self.assertEqual(invoice.state, Invoice.States.PAID.value)

        self.assertTrue(all([c.state == Charge.States.PAID.value for c in invoice.charges.all()]))
