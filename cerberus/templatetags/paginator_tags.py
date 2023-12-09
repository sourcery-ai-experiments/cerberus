# Django
from django import template
from django.core.paginator import Paginator

register = template.Library()


@register.simple_tag
def page_range(paginator: Paginator, number: int, on_each_side: int = 1, on_ends: int = 1):
    try:
        return paginator.get_elided_page_range(number=number, on_each_side=on_each_side, on_ends=on_ends)
    except AttributeError:
        return []


@register.filter()
def is_numeric(value):
    return str(value).isnumeric()


@register.simple_tag(takes_context=True)
def querystring(context, **kwargs):
    request = context["request"]
    updated = request.GET.copy()
    for k, v in kwargs.items():
        if v is not None:
            updated[k] = v
        else:
            updated.pop(k, 0)

    return updated.urlencode()
