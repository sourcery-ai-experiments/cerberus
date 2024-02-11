# Standard Library

# Django
from django.test import TestCase

# Third Party
from model_bakery import baker

# Locals
from ..models import Address, Contact, Customer, Pet
from ..serializers import ContactSerializer, CustomerSerializer


class SerializerTests(TestCase):
    def test_contact(self):
        contact: Contact = baker.make(Contact)
        data = ContactSerializer(instance=contact).data

        validation = {
            "id": contact.pk,
            "type": contact.type.value,
            "name": contact.name,
            "details": contact.details,
        }

        self.assertDictEqual(data, validation)

    def test_customer(self):
        pets: list[Pet] = baker.make(Pet, _quantity=3)
        addresses: list[Address] = baker.make(Address, _quantity=3)
        contacts: list[Contact] = baker.make(Contact, _quantity=3)

        customer: Customer = baker.make(Customer, pets=pets, addresses=addresses, contacts=contacts)

        try:
            data = CustomerSerializer(instance=customer).data
        except Exception as E:
            self.fail(f"Exception raised: {E}")

        validation = {
            "id": customer.pk,
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "name": customer.name,
        }

        self.assertTrue(validation.items() <= data.items())
