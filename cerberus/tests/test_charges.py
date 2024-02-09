# Third Party
import pytest

# Locals
from ..models import Charge


def test_str():
    charge = Charge(name="Test Charge", line=10)
    assert f"{charge}" == "Test Charge - £10.00"


def test_transitions():
    charge = Charge(name="Test Charge", line=1000)
    transitions = list(charge.get_all_state_transitions())

    valid_transitions = {
        ("unpaid", "paid"),
        ("unpaid", "void"),
        ("paid", "refunded"),
    }

    assert {(t.source, t.target) for t in transitions} == valid_transitions
    assert len(valid_transitions) == len(transitions)


@pytest.mark.django_db
def test_paid():
    charge = Charge(name="Test Charge", line=1000)
    charge.save()

    charge.pay()

    assert charge.state == Charge.States.PAID.value
