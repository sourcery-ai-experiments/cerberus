# Standard Library

# Standard Library
from collections.abc import Generator

# Third Party
import pytest
from model_bakery import baker

# Locals
from ..models import Customer


@pytest.fixture
def customer() -> Generator[Customer, None, None]:
    yield baker.make(Customer)


@pytest.mark.django_db
def test_full_name(customer: Customer):
    assert customer.name == f"{customer.first_name} {customer.last_name}"
