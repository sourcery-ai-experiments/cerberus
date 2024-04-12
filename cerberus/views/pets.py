# Django

# Locals
from ..filters import PetFilter
from ..forms import PetForm
from ..models import Pet
from .crud_views import CRUDViews


class PetCRUD(CRUDViews):
    model = Pet
    form_class = PetForm
    filter_class = PetFilter
    sortable_fields = ["name", "customer"]
