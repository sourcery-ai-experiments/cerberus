# Standard Library
from itertools import product

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


def email_name():
    yield "blueberry1234"
    yield "sunflower_87"
    yield "pineapplemaster456"
    yield "techwizard789"
    yield "rainbowsparkle22"


def email_domains():
    yield "example.com"
    yield "mail.co.uk"
    yield "hotmail.fr"
    yield "gmail.net"
    yield "yahoo.co.jp"


@pytest.mark.parametrize("name, domains", product(email_name(), email_domains()))
def test_email_type(name, domains):
    email = f"{name}@{domains}"
    contact = Contact(details=email)
    assert contact.type == Contact.Type.EMAIL
