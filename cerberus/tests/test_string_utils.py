# Third Party
from pytest_django.asserts import assertHTMLEqual

# Locals
from ..templatetags.string_utils import linebreakto, mailto, unslug


def test_mailto_valid_email():
    email = "test@example.com"
    assertHTMLEqual(mailto(email), f'<a href="mailto:{email}">{email}</a>')


def test_mailto_invalid_email():
    email = "not an email"
    assert mailto(email) == email


def test_mailto_empty_string():
    email = ""
    assert mailto(email) == ""


def test_linebreakto_single_line():
    input_str = "Hello world!"
    to_str = "<br>"
    expected_output = "Hello world!"
    assert linebreakto(input_str, to_str) == expected_output


def test_linebreakto_multi_line():
    input_str = "Hello\nworld\n!"
    to_str = "<br>"
    expected_output = "Hello<br>world<br>!"
    assert linebreakto(input_str, to_str) == expected_output


def test_linebreakto_empty_line():
    input_str = ""
    to_str = "<br>"
    expected_output = ""
    assert linebreakto(input_str, to_str) == expected_output


def test_linebreakto_diffrent_to():
    input_str = "Hello\nworld\n!"
    to_str = ", "
    expected_output = "Hello, world, !"
    assert linebreakto(input_str, to_str) == expected_output


def test_linebreakto_trailing_line_break():
    input_str = "Hello world!\n"
    to_str = "<br>"
    expected_output = "Hello world!"
    assert linebreakto(input_str, to_str) == expected_output


def test_linebreakto_():
    input_str = "\n\n\n"
    to_str = "<br>"
    expected_output = "<br><br>"
    assert linebreakto(input_str, to_str) == expected_output

    print("All tests passed successfully!")


def test_unslug_with_single_word():
    input_str = "hello_world"
    expected_output = "hello world"
    assert unslug(input_str) == expected_output


def test_unslug_with_multiple_words():
    input_str = "this_is_a_test"
    expected_output = "this is a test"
    assert unslug(input_str) == expected_output


def test_unslug_with_no_underscores():
    input_str = "hello"
    expected_output = "hello"
    assert unslug(input_str) == expected_output


def test_unslug_with_empty_string():
    input_str = ""
    expected_output = ""
    assert unslug(input_str) == expected_output


def test_unslug_with_special_characters():
    input_str = "special_characters_!@#$%"
    expected_output = "special characters !@#$%"
    assert unslug(input_str) == expected_output


def test_unslug_with_whitespace_only():
    input_str = "   "
    expected_output = "   "
    assert unslug(input_str) == expected_output
