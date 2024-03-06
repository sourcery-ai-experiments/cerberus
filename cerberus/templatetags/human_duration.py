# Standard Library
from datetime import timedelta

# Django
from django import template

# Third Party
import humanize

register = template.Library()


@register.filter
def naturaldelta(duration: timedelta):
    return humanize.naturaldelta(duration)


@register.filter
def precisedelta(duration: timedelta, minimum_unit: str = "minutes"):
    return humanize.precisedelta(duration, suppress=minimum_unit.split(","))
