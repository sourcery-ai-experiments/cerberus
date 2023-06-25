# Django
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("cerberus.urls.urls")),
    path("api/", include("cerberus.urls.api")),
    path("admin/", admin.site.urls),
]
