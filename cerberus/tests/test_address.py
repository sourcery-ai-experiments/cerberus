# Third Party
import pytest

# Locals
from ..models import Address, Customer


@pytest.fixture
def customer():
    return Customer.objects.create(name="Test Customer")


@pytest.fixture
def address(customer):
    return Address.objects.create(
        name="Test Address",
        customer=customer,
        address_line_1="123 Test St",
        town="Test Town",
        county="Test County",
        postcode="12345",
    )


@pytest.mark.django_db
def test_address_creation(address):
    assert isinstance(address, Address)
    assert str(address) == "Test Address"


@pytest.mark.django_db
def test_address_ordering(customer, address):
    address2 = Address.objects.create(
        name="Test Address 2",
        customer=customer,
        address_line_1="456 Test St",
        town="Test Town",
        county="Test County",
        postcode="67890",
    )
    assert Address.objects.first() == address2


@pytest.mark.django_db
def test_address_customer_relationship(address, customer):
    assert address.customer == customer
    assert customer.addresses.first() == address
