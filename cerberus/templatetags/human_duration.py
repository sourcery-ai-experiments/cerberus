# Django
from django import template

# Third Party
import humanize

register = template.Library()


@register.filter
def naturaldelta(duration):
    return humanize.naturaldelta(duration)
