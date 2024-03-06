# Django
from django import template
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter()
def mailto(input: str) -> str:
    try:
        validate_email(input)
        return mark_safe(f'<a href="mailto:{input}">{input}</a>')
    except ValidationError:
        return input


@register.filter
def linebreakto(input: str, to: str) -> str:
    return to.join(input.splitlines())
