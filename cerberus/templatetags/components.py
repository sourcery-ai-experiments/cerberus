# Standard Library
from typing import Any

# Django
from django import template
from django.template import Node, NodeList, TemplateSyntaxError
from django.template.context import Context
from django.template.library import InclusionNode

# Locals
from ..utils import rget

register = template.Library()


def unquote(value: str) -> str:
    return value.strip('"').strip("'")


def parse_extra_context(extra_context: list[str]) -> dict[str, Any]:
    return {unquote(key): value for key, value in (item.split("=") for item in extra_context)}


class ComponentNode(Node):
    extra_context: dict[str, Any]
    template_name: str
    slots: dict[str, NodeList]

    def __init__(self, slots: dict[str, NodeList], template_name: str, extra_context: dict[str, Any] | None = None):
        self.slots = slots
        self.extra_context = extra_context or {}
        self.template_name = template_name

    def render(self, context) -> str:
        extra_context = {}
        for key, value in self.extra_context.items():
            if (value[0] == '"' and value[-1] == '"') or (value[0] == "'" and value[-1] == "'"):
                extra_context[key] = unquote(value)
            else:
                extra_context[key] = rget(context, value, "")

        with context.update(extra_context):
            rendered_slots = {f"slot_{name}": slot.render(context) for name, slot in self.slots.items()}

        inclusion_node = InclusionNode(
            lambda c: {**rendered_slots, **self.extra_context},
            args=[],
            kwargs={},
            takes_context=True,
            filename=self.template_name,
        )

        return inclusion_node.render(context)


class SlotNode(template.Node):
    name: str
    nodelist: NodeList
    extra_context: dict[str, Any]

    def __init__(
        self,
        name: str | None = None,
        nodelist: NodeList | None = None,
        extra_context: dict[str, Any] | None = None,
    ):
        self.name = name or ""
        self.nodelist = nodelist or NodeList()
        self.extra_context = extra_context or {}

    def render(self, context: Context) -> str:
        with context.update(self.extra_context):
            return self.nodelist.render(context)


@register.tag
def slot(parser, token) -> Node:
    args = token.split_contents()
    if len(args) < 2:
        raise TemplateSyntaxError(f"{args[0]} tag requires at least one argument")

    node_list = parser.parse(("endslot",))
    parser.delete_first_token()

    return SlotNode(unquote(args[1]), node_list, parse_extra_context(args[2:]))


@register.tag
def component(parser, token) -> Node:
    node_list = parser.parse(("endcomponent",))
    parser.delete_first_token()

    args = token.split_contents()
    template_name = unquote(args[1])

    slots: dict[str, NodeList] = {"default": NodeList()}
    default_slot = SlotNode(name="default", nodelist=NodeList())

    for node in node_list:
        if isinstance(node, SlotNode):
            slots[node.name] = node.nodelist
        else:
            default_slot.nodelist.append(node)

    slots["default"].append(default_slot)

    return ComponentNode(slots, template_name, parse_extra_context(args[2:]))
