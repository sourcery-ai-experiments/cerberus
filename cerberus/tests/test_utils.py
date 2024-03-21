# Standard Library
import zoneinfo
from datetime import date, datetime

# Django
from django.db import models
from django.utils.timezone import is_aware

# Third Party
import pytest

# Locals
from ..utils import choice_length, make_aware, minimize_whitespace, rgetattr


def test_max_length():
    class TestLength(models.TextChoices):
        ONE = "one", "One"
        TWO = "two", "Two"
        THREE = "three", "Three"
        __empty__ = "empty", "Empty"

    assert choice_length(TestLength) == 5


def test_choice_length():
    class TestLength(models.TextChoices):
        ONE = "one", "One"
        TWO = "two", "Two"
        THREE = "three", "Three"
        __empty__ = "empty", "Empty"

    assert choice_length(TestLength) == 5


def test_make_aware_accepts_dates():
    value = date(2022, 1, 1)
    expected = datetime(2022, 1, 1, tzinfo=zoneinfo.ZoneInfo(key="GMT"))
    assert make_aware(value) == expected


def test_make_aware_adds_timezone():
    value = make_aware(date(2022, 1, 1))
    assert is_aware(value) is True


def test_make_aware_called_twice():
    value = make_aware(date(2022, 1, 1))
    try:
        make_aware(value)
    except Exception as E:
        pytest.fail(f"Exception raised: {E}")


def test_make_does_not_modify_timezone():
    value = make_aware(date(2022, 1, 1), timezone=zoneinfo.ZoneInfo(key="America/New_York"))
    assert value.tzinfo == zoneinfo.ZoneInfo(key="America/New_York")


def test_minimize_whitespace_removes_leading_whitespace():
    value = "    This is a test string"
    expected = "This is a test string"
    assert minimize_whitespace(value) == expected


def test_minimize_whitespace_removes_trailing_whitespace():
    value = "This is a test string    "
    expected = "This is a test string"
    assert minimize_whitespace(value) == expected


def test_minimize_whitespace_removes_newlines():
    value = "This is a test\nstring"
    expected = "This is a teststring"
    assert minimize_whitespace(value) == expected


def test_minimize_whitespace_removes_carriage_returns():
    value = "This is a test\rstring"
    expected = "This is a teststring"
    assert minimize_whitespace(value) == expected


def test_minimize_whitespace_removes_multiple_newlines():
    value = "This is a test\n\nstring"
    expected = "This is a teststring"
    assert minimize_whitespace(value) == expected


def test_minimize_whitespace_removes_multiple_carriage_returns():
    value = "This is a test\r\rstring"
    expected = "This is a teststring"
    assert minimize_whitespace(value) == expected


def test_minimize_whitespace_with_empty_string():
    value = ""
    expected = ""
    assert minimize_whitespace(value) == expected


def test_rgetattr_with_existing_attribute():
    class TestClass:
        def __init__(self):
            self.attr = "value"

    obj = TestClass()
    assert rgetattr(obj, "attr") == "value"


def test_rgetattr_with_nested_existing_attribute():
    class TestClass:
        def __init__(self):
            self.nested = self.Nested()

        class Nested:
            def __init__(self):
                self.attr = "value"

    obj = TestClass()
    assert rgetattr(obj, "nested.attr") == "value"


def test_rgetattr_with_non_existing_attribute():
    class TestClass:
        pass

    obj = TestClass()
    assert rgetattr(obj, "non_existing_attr", "default") == "default"


def test_rgetattr_with_nested_non_existing_attribute():
    class TestClass:
        def __init__(self):
            self.nested = self.Nested()

        class Nested:
            pass

    obj = TestClass()
    assert rgetattr(obj, "nested.non_existing_attr", "default") == "default"
