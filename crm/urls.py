# Django
from django.conf import settings
from django.urls import include, path

# Locals
from .api import router
from .views import CustomerEditView, CustomerListView, PetListView, VetListView

urlpatterns = [
    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework_auth")),
    path("customers/<int:pk>/", CustomerEditView.as_view(), name="customer_edit"),
    path("customers/", CustomerListView.as_view(), name="customers"),
    path("pets/", PetListView.as_view(), name="pets"),
    path("vets/", VetListView.as_view(), name="vets"),
]

if settings.DEBUG:
    # Django
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
