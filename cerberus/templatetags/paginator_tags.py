# Standard Library
from collections.abc import Generator

# Django
from django import template
from django.core.paginator import Paginator

register = template.Library()


def get_pages(paginator: Paginator, number: int | float | str | None, total: int = 7) -> Generator[int, None, None]:
    number = paginator.validate_number(number)

    if paginator.num_pages <= total:
        yield from paginator.page_range
        return

    around: set[int] = set([number])
    while len(around) < total:
        if (n := min(around) - 1) > 0:
            around.add(n)
        if (n := max(around) + 1) <= paginator.num_pages:
            around.add(n)

    yield from around


@register.simple_tag
def page_range(paginator: Paginator, number: int, total: int = 7):
    try:
        return get_pages(paginator, number, total)
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
