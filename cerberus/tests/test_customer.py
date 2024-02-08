# Standard Library
import random

# Third Party
import pytest
from model_bakery import baker
from moneyed import Money

# Locals
from ..models import Customer

baker.generators.add("djmoney.models.fields.MoneyField", lambda: Money(random.uniform(1.0, 100.0), "GBP"))


@pytest.fixture
def customer():
    yield baker.make(Customer)


@pytest.mark.django_db
def test_full_name(customer):
    assert customer.name == f"{customer.first_name} {customer.last_name}"
