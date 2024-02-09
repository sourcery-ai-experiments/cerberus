# Standard Library

# Third Party
import pytest
from model_bakery import baker

# Locals
from ..models import Customer


@pytest.fixture
def customer():
    yield baker.make(Customer)


@pytest.mark.django_db
def test_full_name(customer):
    assert customer.name == f"{customer.first_name} {customer.last_name}"
