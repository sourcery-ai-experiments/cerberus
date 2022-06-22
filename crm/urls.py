# Django
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
