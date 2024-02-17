# Standard Library
from collections.abc import Generator

# Third Party
import pytest
from model_bakery import baker

# Locals
from ..models import Charge, ChargeRefundError


@pytest.fixture
def charge() -> Generator[Charge, None, None]:
    yield baker.make(Charge)


def test_str():
    charge = baker.prepare(Charge, name="Test Charge", amount=10)
    assert f"{charge}" == "Test Charge - £10.00"


def test_transitions():
    charge = baker.prepare(Charge, name="Test Charge", amount=1000)
    transitions = list(charge.get_all_state_transitions())

    valid_transitions = {
        ("unpaid", "paid"),
        ("unpaid", "void"),
    }

    assert {(t.source, t.target) for t in transitions} == valid_transitions
    assert len(valid_transitions) == len(transitions)


@pytest.mark.django_db
def test_paid(charge: Charge):
    charge.pay()

    assert charge.state == Charge.States.PAID.value


@pytest.mark.django_db
def test_full_refund(charge: Charge):
    charge.pay()
    refund_charge = charge.refund()

    assert refund_charge.state == Charge.States.REFUND.value
    assert refund_charge.amount == -charge.amount


@pytest.mark.django_db
def test_partial_refund(charge: Charge):
    charge.pay()
    refund_charge = charge.refund(charge.amount / 2)

    assert refund_charge.state == Charge.States.REFUND.value
    assert -refund_charge.amount == charge.amount / 2


@pytest.mark.django_db
def test_refund_rest(charge: Charge):
    charge.pay()
    refund_charge_1 = charge.refund(1)
    refund_charge_2 = charge.refund()

    refunded = refund_charge_1.amount + refund_charge_2.amount

    assert abs(charge.amount) == abs(refunded)


@pytest.mark.django_db
def test_refund_too_much(charge: Charge):
    charge.pay()

    with pytest.raises(ChargeRefundError):
        charge.refund(charge.amount * 2)


@pytest.mark.django_db
def test_partial_refund_too_much(charge: Charge):
    charge.pay()

    charge.refund(1)

    with pytest.raises(ChargeRefundError):
        charge.refund(charge.amount)
