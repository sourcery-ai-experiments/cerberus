# Django
from django import template
from django.template import Node
from django.template.library import InclusionNode

register = template.Library()


def unquote(value: str) -> str:
    return value.strip('"').strip("'")


class ComponentNode(Node):
    def __init__(self, node_list, template_name: str, extra_context: dict[str, str] | None = None):
        self.node_list = node_list
        self.extra_context = extra_context or {}
        self.template_name = template_name

    def render(self, context) -> str:
        component_block: str = self.node_list.render(context)
        inclusion_node = InclusionNode(
            lambda c: {"component_block": component_block, **self.extra_context},
            args=[],
            kwargs={},
            takes_context=True,
            filename=self.template_name,
        )
        return inclusion_node.render(context)


@register.tag
def component(parser, token) -> Node:
    node_list = parser.parse(("endcomponent",))
    parser.delete_first_token()

    args = token.split_contents()[1:]
    template_name = unquote(args[0])

    context = {}
    for arg in args[1:]:
        key, value = arg.split("=")
        context[f"component_{unquote(key)}"] = unquote(value)

    return ComponentNode(node_list, template_name, context)
