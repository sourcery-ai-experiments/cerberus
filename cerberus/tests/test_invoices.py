# Standard Library
from collections.abc import Generator
from datetime import date, timedelta
from decimal import Decimal

# Django
from django.conf import settings

# Third Party
import pytest
from django_fsm import TransitionNotAllowed
from model_bakery import baker
from moneyed import Money
from xhtml2pdf.context import pisaContext

# Locals
from ..models import Charge, Customer, Invoice, Payment


@pytest.fixture
def customer() -> Generator[Customer, None, None]:
    yield baker.make(Customer, invoice_email="test@example.com")


@pytest.fixture
def invoice(customer) -> Generator[Invoice, None, None]:
    invoice: Invoice = baker.make(Invoice, customer=customer, adjustment=0.0)
    for i in range(3):
        baker.make(Charge, name=f"line {i}", line=10, invoice=invoice)
    yield invoice


@pytest.mark.django_db
def test_overdue(customer):
    today = date.today()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    overdue = baker.make(Invoice, customer=customer, due=yesterday)
    overdue.send()
    loaded_overdue = Invoice.objects.filter(pk=overdue.pk)[0]

    not_due = baker.make(Invoice, customer=customer, due=tomorrow)
    not_due.send()
    loaded_not_due = Invoice.objects.filter(pk=not_due.pk)[0]

    assert loaded_overdue.overdue is True
    assert loaded_not_due.overdue is False

    assert loaded_overdue.overdue == overdue.overdue
    assert loaded_not_due.overdue == not_due.overdue


@pytest.mark.django_db
def test_send_requires_customer():
    inv = baker.make(Invoice)

    with pytest.raises(TransitionNotAllowed):
        inv.send()


@pytest.mark.django_db
def test_send_requires_invoice_email(customer: Customer):
    customer.invoice_email = ""
    inv = baker.make(Invoice, customer=customer)

    with pytest.raises(TransitionNotAllowed):
        inv.send()


@pytest.mark.django_db
def test_can_send(customer: Customer):
    inv = baker.make(Invoice, customer=customer)
    inv.send()

    assert inv.sent_to == customer.invoice_email


@pytest.mark.django_db
def test_cant_update(customer: Customer, invoice: Invoice):
    invoice.send()
    invoice.sent_to = ""
    invoice.save()

    loaded = Invoice.objects.get(pk=invoice.pk)

    assert loaded.sent_to == customer.invoice_email


@pytest.mark.django_db
def test_pdf(invoice: Invoice):
    pdf = invoice.get_pdf()
    assert isinstance(pdf, pisaContext)


@pytest.mark.django_db
def test_change_charges(invoice: Invoice):
    invoice.send()
    assert invoice.state == Invoice.States.UNPAID.value

    invoice.pay()
    assert invoice.state == Invoice.States.PAID.value

    assert all(c.state == Charge.States.PAID.value for c in invoice.charges.all())


@pytest.mark.django_db
def test_loaded_total(invoice):
    loaded_invoice = Invoice.objects.get(pk=invoice.pk)
    assert loaded_invoice.total.amount == invoice.total.amount


@pytest.mark.django_db
def test_available_state_transitions(invoice: Invoice):
    available_state_transitions = invoice.available_state_transitions
    expected_state_transitions = ["send", "void"]
    assert available_state_transitions == expected_state_transitions


@pytest.mark.django_db
def test_loaded_total_with_adjustment(invoice: Invoice):
    invoice.adjustment = Decimal(10)
    invoice.save()
    loaded_invoice = Invoice.objects.get(pk=invoice.pk)
    assert loaded_invoice.total.amount == invoice.total.amount


@pytest.mark.django_db
def test_total(invoice: Invoice):
    loaded_invoice = Invoice.objects.get(pk=invoice.pk)
    assert loaded_invoice.total.amount == invoice.total.amount


@pytest.mark.django_db
def test_create_payment(invoice: Invoice):
    invoice.send()
    invoice.pay()
    payments = sum(p.amount for p in invoice.payments.all())
    assert invoice.total == payments


@pytest.mark.django_db
def test_invoice_paid(invoice: Invoice):
    baker.make(Payment, invoice=invoice, amount=invoice.total / 4)
    baker.make(Payment, invoice=invoice, amount=invoice.total / 4)

    payments = sum(p.amount for p in invoice.payments.all())

    assert payments == invoice.paid


@pytest.mark.django_db
def test_create_partial_payments(invoice: Invoice):
    invoice.send(send_email=False)

    baker.make(Payment, invoice=invoice, amount=invoice.total / 2)

    assert invoice.paid > Money(0, settings.DEFAULT_CURRENCY)
    assert invoice.paid < invoice.total

    invoice.pay()

    assert invoice.paid == invoice.total


@pytest.mark.django_db
def test_totals_match():
    customers = []
    for _ in range(10):
        customers.append(baker.make(Customer, invoice_email="bob@example.com"))

    for i in range(20):
        invoice: Invoice = baker.make(Invoice, customer=customers[i % len(customers)])
        for _ in range(3):
            baker.make(Charge, invoice=invoice)

        invoice.send(send_email=False)

    total_totals = settings.DEFAULT_CURRENCY.zero
    for customer in Customer.objects.all():
        total = settings.DEFAULT_CURRENCY.zero
        for invoice in customer.invoices.all():
            total += invoice.total

        assert customer.invoiced_unpaid == total
        total_totals += total

    assert total_totals > settings.DEFAULT_CURRENCY.zero
