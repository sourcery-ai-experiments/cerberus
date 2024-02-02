# Django
from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag()
def debug_object_dump(var):
    if settings.DEBUG:
        return vars(var)
