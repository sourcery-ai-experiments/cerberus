# Django
from django import template
from django.core.validators import validate_email
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter()
def mailto(email: str) -> str:
    validate_email(email)

    return mark_safe(f'<a href="mailto:{email}">{email}</a>')
