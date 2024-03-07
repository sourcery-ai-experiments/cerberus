# Django
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.shortcuts import resolve_url

# Third Party
from django_htmx.http import HttpResponseClientRedirect


class HtmxLogoutView(auth_views.LogoutView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code in [200, 302, 301] and getattr(request, "htmx", False):
            return HttpResponseClientRedirect(self.next_page)

        return response


def htmx_logout_then_login(request, login_url=None):
    """Log out the user if they are logged in.

    Then redirect to the login page.
    """
    login_url = resolve_url(login_url or settings.LOGIN_URL)
    return HtmxLogoutView.as_view(next_page=login_url)(request)
