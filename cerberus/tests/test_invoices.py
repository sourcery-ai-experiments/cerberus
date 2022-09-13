# Django
from django.test import TestCase

# Third Party
from django_fsm import TransitionNotAllowed
from model_bakery import baker
from xhtml2pdf.context import pisaContext

# Locals
from ..models import Charge, Customer, Invoice


class InvoiceTests(TestCase):
    def setUp(self) -> None:
        self.customer: Customer = baker.make(Customer, invoice_email="test@example.com")
        self.invoice: Invoice = baker.make(Invoice, adjustment=0.0)
        for i in range(3):
            Charge(name=f"line {i}", line=10, quantity=i, invoice=self.invoice)

    def test_send_requires_customer(self):
        inv = Invoice.objects.create()

        with self.assertRaises(TransitionNotAllowed):
            inv.send()

    def test_send_requires_invoice_email(self):
        customer = baker.make(Customer)
        inv = Invoice.objects.create(customer=customer)

        with self.assertRaises(TransitionNotAllowed):
            inv.send()

    def test_can_send(self):
        email = "test@example.com"
        customer = baker.make(Customer, invoice_email=email)
        inv = baker.make(Invoice, customer=customer)

        inv.send()

        self.assertEqual(inv.sent_to, email)

    def test_cant_update(self):
        email = "test@example.com"
        customer = baker.make(Customer, invoice_email=email)
        inv = baker.make(Invoice, customer=customer)

        inv.send()
        inv.sent_to = None
        inv.save()

        loaded = Invoice.objects.get(pk=inv.pk)

        self.assertEqual(loaded.sent_to, email)

    def test_pdf(self):
        pdf = self.invoice.get_pdf()
        self.assertIsInstance(pdf, pisaContext)

    def test_change_charges(self):
        base_invoice = Invoice.objects.create(customer=self.customer)
        base_invoice.save()
        invoice_pk = base_invoice.pk

        charge = Charge.objects.create(name="test charge 1", customer=self.customer, line=12.00, invoice=base_invoice)
        charge.save()

        invoice: Invoice = Invoice.objects.get(pk=invoice_pk)
        self.assertIn(charge, invoice.charges.all())

        invoice.send()
        self.assertEqual(invoice.state, Invoice.States.UNPAID.value)

        invoice.pay()
        self.assertEqual(invoice.state, Invoice.States.PAID.value)

        self.assertTrue(all(c.state == Charge.States.PAID.value for c in invoice.charges.all()))

    def test_available_state_transitions(self):
        invoice = Invoice.objects.create(customer=self.customer)
        invoice.save()

        available_state_transitions = invoice.available_state_transitions
        expected_state_transitions = ["send", "void"]
        self.assertEqual(sorted(available_state_transitions), sorted(expected_state_transitions))

    def test_loaded_total(self):
        invoice = Invoice.objects.create(customer=self.customer)
        invoice.save()

        for _ in range(2):
            charge = Charge(line=10, quantity=1, name="Service", invoice=invoice)
            charge.save()

        loadedInv = Invoice.objects.get(id=invoice.id)
        self.assertEqual(loadedInv.total.amount, 20)

    def test_loaded_total_with_adjustment(self):
        invoice = Invoice.objects.create(customer=self.customer, adjustment=10)
        invoice.save()

        for _ in range(2):
            charge = Charge(line=10, quantity=1, name="Service", invoice=invoice)
            charge.save()

        loadedInv = Invoice.objects.get(id=invoice.id)
        self.assertEqual(loadedInv.total.amount, 30)

    def test_total(self):
        invoice = Invoice.objects.create(customer=self.customer)
        invoice.save()

        for _ in range(2):
            charge = Charge(line=10, quantity=1, name="Service", invoice=invoice)
            charge.save()

        invoice = Invoice.objects.get(id=invoice.id)
        self.assertEqual(invoice.total.amount, 20)
