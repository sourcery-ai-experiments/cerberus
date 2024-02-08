# Django

# Third Party
import pytest

# Locals
from ..models import Contact


def numbers():
    yield "+441234567890"
    yield "01234567890"
    yield "(01234)567890"
    yield "01234 567890"


@pytest.mark.parametrize("number", numbers())
def test_phone_type(number):
    contact = Contact(details=number)
    assert contact.type == Contact.Type.PHONE


def mobile_numbers():
    yield "+447234567890"
    yield "07234567890"
    yield "(07234)567890"
    yield "07234 567890"


@pytest.mark.parametrize("number", mobile_numbers())
def test_mobile_type(number):
    contact = Contact(details=number)
    assert contact.type == Contact.Type.MOBILE


def emails():
    yield "blueberry1234@example.com"
    yield "sunflower_87@mail.com"
    yield "pineapplemaster456@hotmail.com"
    yield "techwizard789@gmail.com"
    yield "rainbowsparkle22@yahoo.com"


@pytest.mark.parametrize("email", emails())
def test_email_type(email):
    contact = Contact(details=email)
    assert contact.type == Contact.Type.EMAIL
