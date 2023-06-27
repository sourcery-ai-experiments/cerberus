# Django
from django import template
from django.core.paginator import Paginator

register = template.Library()


@register.simple_tag
def page_range(paginator: Paginator, number: int, on_each_side: int = 1, on_ends: int = 1):
    return paginator.get_elided_page_range(number=number, on_each_side=on_each_side, on_ends=on_ends)


@register.filter()
def is_numeric(value):
    return str(value).isnumeric()
