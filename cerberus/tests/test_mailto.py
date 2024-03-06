# Third Party
from pytest_django.asserts import assertHTMLEqual

# Locals
from ..templatetags.string_utils import mailto


def test_valid_email():
    email = "test@example.com"
    assertHTMLEqual(mailto(email), f'<a href="mailto:{email}">{email}</a>')


def test_invalid_email():
    email = "not an email"
    assert mailto(email) == email
