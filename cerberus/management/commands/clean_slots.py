# Standard Library
from contextlib import suppress

# Django
from django.core.management.base import BaseCommand
from django.db.models import ProtectedError

# Locals
from ...models import BookingSlot


class Command(BaseCommand):
    help = "Clean empty booking slots"

    def handle(self, *args, **options):
        self.stdout.write("Removing empty booking slots")

        for slot in BookingSlot.objects.all():
            with suppress(ProtectedError):
                slot.delete()
                self.stdout.write("Removed slot")
