# Django
from django import template
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
    if hasattr(model, "_meta"):
        return model._meta.verbose_name
    return ""


@register.filter
def verbose_name_plural(model):
    if hasattr(model, "_meta"):
        return model._meta.verbose_name_plural
    return ""
