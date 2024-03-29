# Django
from django import template
from django.contrib.staticfiles.storage import staticfiles_storage
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def include_static(file_name: str) -> str:
    file = staticfiles_storage.path(file_name)
    with open(file) as f:
        return mark_safe(f.read())
