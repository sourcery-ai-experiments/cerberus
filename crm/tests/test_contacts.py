# Django
from django.test import TestCase

# Locals
from ..models import Contact


class test_contacts(TestCase):
    def test_phone_type(self):
        numbers = [
            "+441234567890",
            "01234567890",
            "(01234)567890",
            "01234 567890",
        ]

        for number in numbers:
            contact = Contact(details=number)
            self.assertEqual(contact.type, Contact.Type.PHONE)

    def test_mobile_type(self):
        numbers = [
            "+447234567890",
            "07234567890",
            "(07234)567890",
            "07234 567890",
        ]

        for number in numbers:
            contact = Contact(details=number)
            self.assertEqual(contact.type, Contact.Type.MOBILE)

    def test_email_type(self):
        contact = Contact(details="bob@example.com")
        self.assertEqual(contact.type, Contact.Type.EMAIL)
