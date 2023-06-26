# Standard Library

# Standard Library
import re

# Django
from django.core.management.base import BaseCommand

# Third Party
from faker import Faker

# First Party
from cerberus.models import Customer


class Command(BaseCommand):
    help = "Anonymise customer data"

    def handle(self, *args, **options):
        self.stdout.write("Anonymising customer data")
        fake = Faker("en_GB")

        titles = "|".join(["Sir", "Madam", "Mr", "Mrs", "Ms", "Miss", "Dr", "Professor"])
        regex = re.compile(rf"^({titles})\s+", re.IGNORECASE)

        for customer in Customer.objects.all():
            name_parts = regex.sub("", f"{fake.name()}").split(" ")
            customer.first_name = name_parts[0]
            customer.last_name = name_parts[-1]
            customer.other_names = " ".join(name_parts[1:-1])
            customer.save()
