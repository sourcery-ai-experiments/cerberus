# Django
from django.core.exceptions import ValidationError

# Third Party
import pytest
from pytest_django.asserts import assertHTMLEqual

# Locals
from ..templatetags.mailto import mailto


def test_valid_email():
    email = "test@example.com"
    assertHTMLEqual(mailto(email), f'<a href="mailto:{email}">{email}</a>')


def test_invalid_email():
    email = "not an email"
    with pytest.raises(ValidationError):
        mailto(email)
