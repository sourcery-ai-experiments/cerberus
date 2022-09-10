# Standard Library
import random
import re

# Django
from django.core.management.base import BaseCommand
from django.db import IntegrityError

# Third Party
from faker import Faker

# First Party
from cerberus.models import Contact, Customer, Pet, Vet


class Command(BaseCommand):
    help = "Create some dummy data"

    def handle(self, *args, **options):
        self.stdout.write("Creating some dummy data")
        fake = Faker("en_GB")

        vet_count = 10
        customer_count = 200
        pet_count = int(customer_count * 1.5)

        for _ in range(vet_count - Vet.objects.count()):
            vet = Vet.objects.create(name=fake.company(), phone=fake.phone_number())
            self.stdout.write(f"Created vet {vet.name}")

        vets = Vet.objects.all()
        titles = "|".join(["Sir", "Madam", "Mr", "Mrs", "Ms", "Miss", "Dr", "Professor"])
        regex = re.compile(rf"^({titles})\s+", re.IGNORECASE)

        for _ in range(customer_count - Customer.objects.count()):
            customer = Customer.objects.create(vet=random.choice(vets))
            name_parts = regex.sub("", f"{fake.name()}").split(" ")
            customer.first_name = name_parts[0]
            customer.last_name = name_parts[-1]
            customer.other_names = " ".join(name_parts[1:-1])
            customer.save()

            self.stdout.write(f"Created customer {customer.name}")

        customers = Customer.objects.all()

        for customer in customers:
            r = random.Random()
            r.seed(customer.id)
            for _ in range(r.randint(0, 5) - customer.contacts.count()):
                try:
                    Contact.objects.create(
                        customer=customer,
                        name=random.choice(["Home", "Work", "Mobile", fake.name()]),
                        details=fake.phone_number() if fake.pybool() else fake.ascii_email(),
                    )
                except IntegrityError:
                    pass

        for _ in range(pet_count - Pet.objects.count()):
            if fake.pybool():
                name = fake.first_name_male()
                sex = Pet.Sex.MALE.value
            else:
                name = fake.first_name_female()
                sex = Pet.Sex.FEMALE.value

            pet = Pet.objects.create(
                name=name,
                sex=sex,
                customer=random.choice(customers),
                vet=random.choice(vets),
                dob=fake.date_of_birth(tzinfo=None, minimum_age=0, maximum_age=15),
                description=fake.text(max_nb_chars=200),
                treatment_limit=fake.pyint(min_value=0, max_value=1000) * 10,
                medical_conditions=fake.text(max_nb_chars=200) if fake.pybool() else "",
                allergies=fake.text(max_nb_chars=200) if fake.pybool() else "",
            )
            self.stdout.write(f"Created pet {pet.name}")
