# Django
from django import template
from django.utils.safestring import mark_safe
from django.utils.text import capfirst

register = template.Library()


@register.filter()
def fields(model):
    for field in model._meta.get_fields():
        value = getattr(model, field.name, None)
        try:
            yield capfirst(field.verbose_name), value
        except AttributeError:
            yield capfirst(field.name), value


@register.filter
def verbose_name(model):
    return model._meta.verbose_name if hasattr(model, "_meta") else ""


@register.filter
def verbose_name_plural(model):
    return model._meta.verbose_name_plural if hasattr(model, "_meta") else ""


@register.simple_tag
def filter_code(field_name):
    return mark_safe(
        f"x-on:click=\"sort_order = sort_order == 'desc' || sort != '{field_name}' ? 'asc' : 'desc';sort = '{field_name}';$nextTick(() => {{htmx.trigger('.filter-form', 'change');}})\""  # noqa: E501
    )
