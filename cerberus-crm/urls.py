# Django
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path("", include("cerberus.urls.urls")),
    path("api/", include("cerberus.urls.api")),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.logout_then_login, name="logout"),
    path("admin/", admin.site.urls),
]
