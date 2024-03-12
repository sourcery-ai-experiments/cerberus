# Standard Library
import calendar

# Django
from django import template

register = template.Library()


@register.filter()
def day_of_week(value: int) -> str:
    days = list(calendar.day_name)
    return days[value]
