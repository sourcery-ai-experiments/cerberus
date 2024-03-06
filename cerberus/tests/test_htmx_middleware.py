# Django
from django.http import HttpResponse
from django.test import RequestFactory

# Third Party
import pytest

# Locals
from ..middleware import HtmxVaryHeaderMiddleware


@pytest.fixture
def middleware():
    def mock_get_response(_request):
        return HttpResponse()

    return HtmxVaryHeaderMiddleware(mock_get_response)


def test_htmx_vary_header_set_when_htmx_header_true(middleware):
    request = RequestFactory().get("/")
    setattr(request, "htmx", True)

    response = middleware(request)

    assert "HX-Request" in response["Vary"]


def test_htmx_vary_header_not_set_when_htmx_header_false(middleware):
    request = RequestFactory().get("/")
    setattr(request, "htmx", False)

    response = middleware(request)

    assert "HX-Request" not in getattr(response, "Vary", [])


def test_htmx_vary_header_not_set_when_htmx_header_not_present(middleware):
    request = RequestFactory().get("/")

    response = middleware(request)

    assert "HX-Request" not in getattr(response, "Vary", [])
