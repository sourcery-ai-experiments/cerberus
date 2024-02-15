# Django
from django.db.models import GeneratedField

# Third Party
import pytest
from hypothesis import given
from hypothesis.extra.django import from_model, register_field_strategy
from hypothesis.strategies import just
from model_bakery import baker

# Locals
from ..models import Address, Contact, Customer, Pet
from ..serializers import ContactSerializer, CustomerSerializer

register_field_strategy(GeneratedField, just(None))


@pytest.mark.django_db
@given(customer=from_model(Customer))
def test_customer_can_serialize(customer: Customer):
    try:
        dict(CustomerSerializer(instance=customer).data)
    except Exception as E:
        pytest.fail(f"Exception raised: {E}")


@pytest.mark.django_db
@given(contact=from_model(Contact, customer=from_model(Customer)))
def test_contact_can_serialize(contact: Contact):
    try:
        dict(ContactSerializer(instance=contact).data)
    except Exception as E:
        pytest.fail(f"Exception raised: {E}")


@pytest.mark.django_db
def test_contact():
    contact: Contact = baker.make(Contact)
    data = ContactSerializer(instance=contact).data

    validation = {
        "id": contact.pk,
        "type": contact.type.value,
        "name": contact.name,
        "details": contact.details,
    }

    assert data == validation


@pytest.mark.django_db
def test_customer():
    pets: list[Pet] = baker.make(Pet, _quantity=3)
    addresses: list[Address] = baker.make(Address, _quantity=3)
    contacts: list[Contact] = baker.make(Contact, _quantity=3)

    customer: Customer = baker.make(Customer, pets=pets, addresses=addresses, contacts=contacts)

    try:
        data = dict(CustomerSerializer(instance=customer).data)
    except Exception as E:
        pytest.fail(f"Exception raised: {E}")

    validation = {
        "id": customer.pk,
        "first_name": customer.first_name,
        "last_name": customer.last_name,
        "name": customer.name,
    }

    assert validation.items() <= data.items()
