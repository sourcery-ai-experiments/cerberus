# Django
from django.urls import reverse


def nav_links(request):
    return {
        "crm_nav_links": [
            {"title": "Customers", "url": reverse("customers")},
            {"title": "Pets", "url": reverse("pets")},
            {"title": "Vets", "url": reverse("vets")},
        ]
    }
