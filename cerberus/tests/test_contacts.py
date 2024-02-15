# Standard Library
from collections.abc import Generator
from itertools import product

# Third Party
import pytest
from hypothesis import given
from hypothesis import strategies as st

# Locals
from ..models import Contact


def numbers() -> Generator[str, None, None]:
    yield "+441234567890"
    yield "01234567890"
    yield "(01234)567890"
    yield "01234 567890"


@pytest.mark.parametrize("number", numbers())
def test_phone_type(number: str):
    contact = Contact(details=number)
    assert contact.type == Contact.Type.PHONE


def mobile_numbers() -> Generator[str, None, None]:
    yield "+447234567890"
    yield "07234567890"
    yield "(07234)567890"
    yield "07234 567890"


@pytest.mark.parametrize("number", mobile_numbers())
def test_mobile_type(number: str):
    contact = Contact(details=number)
    assert contact.type == Contact.Type.MOBILE


def email_name() -> Generator[str, None, None]:
    yield "blueberry1234"
    yield "sunflower_87"
    yield "pineapplemaster456"
    yield "techwizard789"
    yield "rainbowsparkle22"


def email_domains() -> Generator[str, None, None]:
    yield "example.com"
    yield "mail.co.uk"
    yield "hotmail.fr"
    yield "gmail.net"
    yield "yahoo.co.jp"


@pytest.mark.parametrize("name, domains", product(email_name(), email_domains()))
def test_email_type(name: str, domains: str):
    email = f"{name}@{domains}"
    contact = Contact(details=email)
    assert contact.type == Contact.Type.EMAIL


@given(st.emails())
def test_more_email_type(email: str):
    contact = Contact(details=email)
    assert contact.type == Contact.Type.EMAIL
