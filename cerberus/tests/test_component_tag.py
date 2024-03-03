# Django
from django.template import Context, Template

# Third Party
import pytest
from pytest_django.asserts import assertHTMLEqual


@pytest.fixture
def render_template():
    def _render_template(template: str, context: dict[str, str] | None = None) -> str:
        return Template(template).render(Context(context or {}))

    yield _render_template


@pytest.fixture(autouse=True)
def component_template(tmp_path, settings):
    settings.TEMPLATES[0]["DIRS"] += [tmp_path]

    with open(tmp_path / "test.html", "w") as f:
        f.write(
            """
<div>
    <h1>{{ component_title }}</h1>
    <p>{{ component_block }}</p>
</div>
"""
        )


@pytest.fixture
def template():
    yield """
{% load components %}

<section>
    {% component "test.html" title="title" %}
        this is body text
    {% endcomponent %}
</section>
"""


def test_renders_component(render_template, template):
    output = render_template(template)
    assertHTMLEqual(
        output,
        """
<section>
    <div>
        <h1>title</h1>
        <p>this is body text</p>
    </div>
</section>
""",
    )


def test_extra_context(render_template, template):
    output = render_template(template, {"title": "Main Title"})
    assertHTMLEqual(
        output,
        """
<section>
    <div>
        <h1>title</h1>
        <p>this is body text</p>
    </div>
</section>
""",
    )
