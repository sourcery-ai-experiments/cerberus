# Django
from django import template

register = template.Library()


@register.filter()
def day_of_week(value: int) -> str:
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return days[value]
