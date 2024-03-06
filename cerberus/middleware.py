# Standard Library
from collections.abc import Callable

# Django
from django.http import HttpRequest, HttpResponse
from django.utils.cache import patch_vary_headers


class HtmxVaryHeaderMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)

        if getattr(request, "htmx", False):
            patch_vary_headers(response, ("HX-Request",))

        return response
