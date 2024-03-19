# Standard Library
import zoneinfo
from datetime import date, datetime

# Django
from django.db import models
from django.utils.timezone import is_aware

# Third Party
import pytest

# Locals
from ..utils import choice_length, make_aware


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
