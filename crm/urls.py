# Django
from django.conf import settings
from django.urls import include, path

# Locals
from . import reports
from .api import router

urlpatterns = [
    path("api/reports/", include(reports.urls)),
    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework_auth")),
]

if settings.DEBUG:
    # Django
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
