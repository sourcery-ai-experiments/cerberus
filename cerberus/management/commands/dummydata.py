# Standard Library
import random
import re
from datetime import datetime, timedelta

# Django
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django.db.models import QuerySet
from django.utils.timezone import make_aware

# Third Party
from faker import Faker

# First Party
from cerberus.models import Charge, Contact, Customer, Invoice, Pet, Vet

try:
    # Third Party
    from freezegun import freeze_time

    has_freezegun = True
except ModuleNotFoundError:
    has_freezegun = False


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
            customer.invoice_email = fake.email()
            customer.invoice_address = fake.address()
            customer.save()

            self.stdout.write(f"Created customer {customer.name}")

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

        if has_freezegun:
            services = [
                {"name": "Walk", "cost": 12},
                {"name": "Solo Walk", "cost": 24},
                {"name": "Dropin", "cost": 10},
            ]
            invoice_per_week = 10
            invoice_weeks = 10

            for weeks in range(invoice_weeks, -1, -1):
                date = datetime.now() - timedelta(weeks=weeks)
                start = date - timedelta(days=date.weekday())
                end = start + timedelta(days=6)

                invoice_count = Invoice.objects.filter(created__gte=make_aware(start), created__lte=make_aware(end)).count()

                with freeze_time(date):
                    for _ in range(invoice_per_week - invoice_count):
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
                                amount=service["cost"], quantity=random.randrange(1, 5), name=service["name"], invoice=invoice
                            )
                            charge.save()

                        stage = random.randrange(1, 5)
                        if stage >= 1:
                            invoice.send(send_email=False)

                        if stage >= 2:
                            invoice.pay()
