from django.conf import settings
from django.urls import include, path
from neapolitan.views import CRUDView

from .. import views
#from ..views import dashboard, ListCustomer
from ..models import Customer, Contact, Pet
from ..serializers import PetSerializer



urlpatterns = [
    path("", views.dashboard, name="dashboard"),
] + views.CustomerCRUD.get_urls()
