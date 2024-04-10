# Standard Library
import random
import re
from datetime import datetime, timedelta

# Django
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django.db.models import QuerySet

# Third Party
from faker import Faker

# Locals
from ...models import Charge, Contact, Customer, Invoice, Pet, Service, Vet
from ...utils import make_aware

try:
    # Third Party
    from freezegun import freeze_time

    has_freezegun = True
except ModuleNotFoundError:
    has_freezegun = False


class Command(BaseCommand):
    help = "Create some dummy data"

    vet_count = 10
    customer_count = 200
    pet_count = 300
    invoice_per_week = 10
    invoice_weeks = 10

    def handle(self, *args, **options):
        self.stdout.write("Creating some dummy data")
        self.create_dummy_vets()
        self.create_dummy_customers()
        self.create_dummy_contacts()
        self.create_dummy_pets()
        self.create_dummy_invoices()
        self.create_dummy_services()

    def create_dummy_services(self):
        fake = Faker("en_GB")

        walk_defaults = {
            "cost": 12,
            "length": timedelta(minutes=60),
            "booked_length": timedelta(minutes=120),
            "max_pet": 4,
        }
        fake.color

        services = [
            {"name": "Walk", "max_customer": 4, "display_colour": "#00ad3d", **walk_defaults},
            {"name": "Solo Walk", "max_customer": 1, "display_colour": "#0025e0", **walk_defaults},
            {
                "name": "Dropin",
                "max_customer": 1,
                "max_pet": 1,
                "cost": 10,
                "display_colour": "#cc8b00",
                "length": timedelta(minutes=30),
                "booked_length": timedelta(minutes=60),
            },
        ]
        for service in services:
            Service.objects.get_or_create(name=service["name"], defaults=service)

    def create_dummy_vets(self):
        fake = Faker("en_GB")

        for _ in range(self.vet_count - Vet.objects.count()):
            vet = Vet.objects.create(name=fake.company(), phone=fake.phone_number())
            self.stdout.write(f"Created vet {vet.name}")

    def create_dummy_customers(self):
        fake = Faker("en_GB")
        vets = Vet.objects.all()
        titles = "|".join(["Sir", "Madam", "Mr", "Mrs", "Ms", "Miss", "Dr", "Professor"])
        regex = re.compile(rf"^({titles})\s+", re.IGNORECASE)

        for _ in range(self.customer_count - Customer.objects.count()):
            customer = Customer.objects.create(vet=random.choice(vets))
            name_parts = regex.sub("", f"{fake.name()}").split(" ")
            customer.first_name = name_parts[0]
            customer.last_name = name_parts[-1]
            customer.other_names = " ".join(name_parts[1:-1])
            customer.invoice_email = fake.email()
            customer.invoice_address = fake.address()
            customer.save()

            self.stdout.write(f"Created customer {customer.first_name} {customer.last_name}")

    def create_dummy_contacts(self):
        fake = Faker("en_GB")
        customers: QuerySet[Customer] = Customer.objects.all()

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

    def create_dummy_pets(self):
        fake = Faker("en_GB")
        customers: QuerySet[Customer] = Customer.objects.all()
        vets = Vet.objects.all()

        for _ in range(self.pet_count - Pet.objects.count()):
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

    def create_dummy_invoices(self):
        fake = Faker("en_GB")
        customers = Customer.objects.all()
        if has_freezegun:
            services = [
                {"name": "Walk", "cost": 12},
                {"name": "Solo Walk", "cost": 24},
                {"name": "Dropin", "cost": 10},
            ]

            for weeks in range(self.invoice_weeks, -1, -1):
                date = datetime.now() - timedelta(weeks=weeks)
                start = date - timedelta(days=date.weekday())
                end = start + timedelta(days=6)

                invoice_count = Invoice.objects.filter(
                    created__gte=make_aware(start), created__lte=make_aware(end)
                ).count()

                with freeze_time(date):
                    for _ in range(self.invoice_per_week - invoice_count):
                        self.stdout.write("Creating invoice")

                        customer = random.choice(customers)
                        if customer.invoice_email == "":
                            customer.invoice_email = fake.ascii_email()
                            customer.save()

                        adjustment = random.choice([0, 0, 0, 0, 0, random.choice([2, 10, 12.5, 20])])
                        invoice: Invoice = Invoice.objects.create(customer=customer, adjustment=adjustment)
                        invoice.save()

                        for _ in range(random.randrange(1, 5)):
                            service = random.choice(services)
                            charge = Charge(
                                line=service["cost"],
                                quantity=random.randrange(1, 5),
                                name=service["name"],
                                invoice=invoice,
                            )
                            charge.save()

                        stage = random.randrange(1, 5)
                        if stage >= 1:
                            invoice.send(send_email=False)

                        if stage >= 2:
                            invoice.pay()
