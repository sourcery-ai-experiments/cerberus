# Standard Library
import contextlib
from collections import Counter

# Django
from django.core.management.base import BaseCommand

# First Party
from cerberus.exceptions import InvalidEmail
from cerberus.models import Contact, Customer


class Command(BaseCommand):
    help = "Create some dummy data"

    def handle(self, *args, **options):
        self.stdout.write("Fixing as many customers it can")

        for customer in Customer.objects.all():
            if customer.invoice_email == "":
                counts = Counter([c.type for c in customer.contacts.all()])
                if counts[Contact.Type.EMAIL] == 1:
                    self.stdout.write(f"Can fix invoice email for {customer.name}")
                    for contact in customer.contacts.all():
                        with contextlib.suppress(InvalidEmail):
                            contact.set_as_invoice()
