# Django
from django.template import Context, Template
from django.template.engine import Engine

# Third Party
import pytest
from pytest_django.asserts import assertHTMLEqual


@pytest.fixture
def render_template():
    def _render_template(template: str, context: dict[str, str] | None = None) -> str:
        rendered = Template(template).render(Context(context or {}))
        return rendered

    yield _render_template


@pytest.fixture(autouse=True)
def component_template(tmp_path, settings):
    if tmp_path not in settings.TEMPLATES[0]["DIRS"]:
        settings.TEMPLATES[0]["DIRS"] += [tmp_path]
    engine = Engine.get_default()
    if tmp_path not in engine.dirs:
        engine.dirs += [tmp_path]

    with open(tmp_path / "test.html", "w") as f:
        f.write(
            """
<div>
    <h1>{{ title }}</h1>
    <p>{{ slot_default }}</p>

    {% if slot_footer %}
    <footer>{{ slot_footer }}</footer>
    {% endif %}
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


@pytest.fixture
def template_with_footer(template):
    yield """
{% load components %}

<section>
    {% component "test.html" title="title" %}
        this is body text
        {% slot footer %}footer text{% endslot %}
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


def test_slot_footer(render_template, template_with_footer):
    output = render_template(template_with_footer)
    assertHTMLEqual(
        output,
        """
<section>
    <div>
        <h1>title</h1>
        <p>this is body text</p>
        <footer>footer text</footer>
    </div>
</section>
""",
    )
