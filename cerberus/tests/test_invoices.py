# Standard Library
from datetime import date, timedelta

# Django
from django.test import TestCase

# Third Party
from django_fsm import TransitionNotAllowed
from model_bakery import baker
from moneyed import Money
from xhtml2pdf.context import pisaContext

# Locals
from ..models import Charge, Customer, Invoice, Payment


class InvoiceTests(TestCase):
    def setUp(self) -> None:
        self.customer: Customer = baker.make(Customer, invoice_email="test@example.com")
        self.invoice: Invoice = baker.make(Invoice, adjustment=0.0)
        for i in range(3):
            Charge(name=f"line {i}", line=10, quantity=i, invoice=self.invoice)

    def test_overdue(self):
        today = date.today()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        email = "test@example.com"
        customer = baker.make(Customer, invoice_email=email)
        overdue = baker.make(Invoice, customer=customer, due=yesterday)
        overdue.send()
        loaded_overdue = Invoice.objects.filter(pk=overdue.pk)[0]

        notdue = baker.make(Invoice, customer=customer, due=tomorrow)
        notdue.send()
        loaded_notdue = Invoice.objects.filter(pk=notdue.pk)[0]

        self.assertTrue(loaded_overdue.overdue)
        self.assertFalse(loaded_notdue.overdue)

        self.assertEqual(loaded_overdue.overdue, overdue.overdue)
        self.assertEqual(loaded_notdue.overdue, notdue.overdue)

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

    def create_invoice(self, charge_count=2, charge_amount=10, adjustment=0) -> Invoice:
        invoice = Invoice.objects.create(customer=self.customer, adjustment=adjustment)
        invoice.save()

        for _ in range(charge_count):
            charge = Charge(line=charge_amount, quantity=1, name="Service", invoice=invoice)
            charge.save()

        return invoice

    def test_loaded_total(self):
        invoice = self.create_invoice()

        loadedInv = Invoice.objects.get(pk=invoice.pk)
        self.assertEqual(loadedInv.total.amount, 20)

    def test_loaded_total_with_adjustment(self):
        invoice = self.create_invoice(adjustment=10)

        loadedInv = Invoice.objects.get(pk=invoice.pk)
        self.assertEqual(loadedInv.total.amount, 30)

    def test_total(self):
        invoice = self.create_invoice()

        invoice = Invoice.objects.get(pk=invoice.pk)
        self.assertEqual(invoice.total.amount, 20)

    def test_create_payment(self):
        invoice = self.create_invoice()

        invoice.send(send_email=False)
        invoice.pay()

        payments = sum(p.amount for p in invoice.payments.all())
        self.assertEqual(invoice.total, payments)

    def test_invoice_paid(self):
        invoice = self.create_invoice()

        Payment.objects.create(invoice=invoice, amount=invoice.total / 4)
        Payment.objects.create(invoice=invoice, amount=invoice.total / 4)

        payments = sum(p.amount for p in invoice.payments.all())

        self.assertEqual(payments, invoice.paid)

    def test_create_partial_payments(self):
        invoice = self.create_invoice()
        invoice.send(send_email=False)

        Payment.objects.create(invoice=invoice, amount=invoice.total / 2)

        self.assertGreater(invoice.paid, Money(0, "GBP"))
        self.assertLess(invoice.paid, invoice.total)

        invoice.pay()

        self.assertEqual(invoice.paid, invoice.total)

    def test_complex_totals(self):
        invoice: Invoice = Invoice.objects.create(customer=self.customer)
        invoice.save()

        Charge.objects.create(line=15, quantity=2, invoice=invoice)
        Charge.objects.create(line=10, quantity=3, invoice=invoice)

        invoice.send(send_email=False)

        self.assertEqual(invoice.total, Money(60, "GBP"))

    def test_totals_match(self):
        customers = []
        for _ in range(10):
            customer: Customer = baker.make(Customer, invoice_email="bob@example.com")
            customers.append(customer)

        for i in range(20):
            invoice: Invoice = baker.make(Invoice, customer=customers[i % len(customers)])
            for _ in range(3):
                baker.make(Charge, invoice=invoice)

            invoice.send(send_email=False)

        total_totals = Money(0, "GBP")
        for customer in Customer.objects.all():
            total = Money(0, "GBP")
            for invoice in customer.invoices.all():
                total += invoice.total

            self.assertEqual(customer.invoiced_unpaid, total)
            total_totals += total

        self.assertGreater(total_totals, Money(0, "GBP"))
