# Standard Library
import random

# Django
from django.core.management.base import BaseCommand

# Third Party
from faker import Faker

# First Party
from crm.models import Contact, Customer, Pet, Vet


class Command(BaseCommand):
    help = "Create some dummy data"

    def handle(self, *args, **options):
        self.stdout.write("Creating some dummy data")
        fake = Faker("en_GB")

        vet_count = 10
        customer_count = 50
        pet_count = int(customer_count * 1.25)
        contact_count = int(customer_count * 1.25)

        for _ in range(vet_count - Vet.objects.count()):
            vet = Vet.objects.create(name=fake.company(), phone=fake.phone_number())
            self.stdout.write(f"Created vet {vet.name}")

        vets = Vet.objects.all()
        for _ in range(customer_count - Customer.objects.count()):
            customer = Customer.objects.create(name=fake.name(), vet=random.choice(vets))
            self.stdout.write(f"Created vet {customer.name}")

        customers = Customer.objects.all()

        for _ in range(contact_count - Contact.objects.count()):
            Contact.objects.create(
                customer=random.choice(customers),
                name=random.choice(["Home", "Work", "Mobile", fake.name()]),
                details=fake.phone_number() if fake.pybool() else fake.ascii_email(),
            )

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
                microchipped=fake.pybool(),
                off_lead_consent=fake.pybool(),
                vaccinated=fake.pybool(),
                flead_wormed=fake.pybool(),
                insured=fake.pybool(),
                leucillin=fake.pybool(),
                noise_sensitive=fake.pybool(),
            )
            self.stdout.write(f"Created pet {pet.name}")
