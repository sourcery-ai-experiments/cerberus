# Standard Library
from collections.abc import Callable, Generator
from datetime import datetime, timedelta
from functools import partial

# Django
from django.db.utils import IntegrityError
from django.test import TestCase

# Third Party
import pytest
from model_bakery import baker

# Locals
from ..exceptions import BookingSlotMaxCustomers, BookingSlotMaxPets
from ..models import Booking, BookingSlot, Charge, Customer, Pet, Service


@pytest.fixture
def walk_service() -> Generator[Service, None, None]:
    yield baker.make(Service, max_pet=4, max_customer=4)


@pytest.fixture
def customer() -> Generator[Customer, None, None]:
    yield baker.make(Customer)


@pytest.fixture
def make_pet(customer: Customer) -> Generator[Callable[[], Pet], None, None]:
    yield partial(baker.make, Pet, customer=customer)


def test_start_before_end():
    slot = BookingSlot(
        start=BookingSlot.round_date_time(datetime.now() + timedelta(hours=2)),
        end=BookingSlot.round_date_time(datetime.now() + timedelta(hours=4)),
    )

    assert slot._valid_dates() is True


def test_end_before_start():
    slot = BookingSlot(
        start=BookingSlot.round_date_time(datetime.now() + timedelta(hours=4)),
        end=BookingSlot.round_date_time(datetime.now() + timedelta(hours=2)),
    )

    assert slot._valid_dates() is False


@pytest.mark.django_db
def test_has_overlap(walk_service, make_pet):
    Booking.objects.create(
        cost=0,
        start=BookingSlot.round_date_time(datetime.now() + timedelta(hours=1)),
        end=BookingSlot.round_date_time(datetime.now() + timedelta(hours=3)),
        service=walk_service,
        pet=make_pet(),
    )

    slot = BookingSlot(
        start=BookingSlot.round_date_time(datetime.now() + timedelta(hours=2)),
        end=BookingSlot.round_date_time(datetime.now() + timedelta(hours=4)),
    )

    assert slot.overlaps() is True


@pytest.mark.django_db
def test_does_not_have_overlap(walk_service, make_pet):
    Booking.objects.create(
        cost=0,
        start=BookingSlot.round_date_time(datetime.now() + timedelta(hours=2)),
        end=BookingSlot.round_date_time(datetime.now() + timedelta(hours=3)),
        service=walk_service,
        pet=make_pet(),
    )

    slot = BookingSlot(
        start=BookingSlot.round_date_time(datetime.now() + timedelta(hours=5)),
        end=BookingSlot.round_date_time(datetime.now() + timedelta(hours=6)),
    )

    assert slot.overlaps() is False


@pytest.mark.django_db
def test_get_existing_slot():
    slot = BookingSlot.objects.create(
        start=BookingSlot.round_date_time(datetime.now() + timedelta(hours=1)),
        end=BookingSlot.round_date_time(datetime.now() + timedelta(hours=3)),
    )
    sameSlot = BookingSlot.get_slot(start=slot.start, end=slot.end)

    assert sameSlot.id == slot.id


@pytest.mark.django_db
def test_no_duplicates():
    slot = BookingSlot.objects.create(
        start=BookingSlot.round_date_time(datetime.now() + timedelta(hours=1)),
        end=BookingSlot.round_date_time(datetime.now() + timedelta(hours=3)),
    )

    with pytest.raises(IntegrityError):
        emptySlot = BookingSlot(start=slot.start, end=slot.end)

        emptySlot.save()


@pytest.mark.django_db
def test_pet_count(walk_service, make_pet):
    booking1 = Booking.objects.create(
        cost=0,
        start=BookingSlot.round_date_time(datetime.now() + timedelta(hours=5)),
        end=BookingSlot.round_date_time(datetime.now() + timedelta(hours=6)),
        service=walk_service,
        pet=make_pet(),
    )

    Booking.objects.create(
        cost=0,
        start=BookingSlot.round_date_time(datetime.now() + timedelta(hours=5)),
        end=BookingSlot.round_date_time(datetime.now() + timedelta(hours=6)),
        service=walk_service,
        pet=make_pet(),
    )

    assert booking1.booking_slot.pet_count == 2


@pytest.mark.django_db
def test_customer_count(walk_service, make_pet):
    booking1 = Booking.objects.create(
        cost=0,
        start=BookingSlot.round_date_time(datetime.now() + timedelta(hours=5)),
        end=BookingSlot.round_date_time(datetime.now() + timedelta(hours=6)),
        service=walk_service,
        pet=make_pet(),
    )
    booking1.save()

    Booking.objects.create(
        cost=0,
        start=BookingSlot.round_date_time(datetime.now() + timedelta(hours=5)),
        end=BookingSlot.round_date_time(datetime.now() + timedelta(hours=6)),
        service=walk_service,
        pet=make_pet(),
    ).save()

    assert booking1.booking_slot.customer_count == 1


@pytest.mark.django_db
def test_no_pet_count():
    slot = BookingSlot.objects.create(
        start=BookingSlot.round_date_time(datetime.now() + timedelta(hours=1)),
        end=BookingSlot.round_date_time(datetime.now() + timedelta(hours=3)),
    )
    assert slot.pet_count == 0


@pytest.mark.django_db
def test_no_customer_count():
    slot = BookingSlot.objects.create(
        start=BookingSlot.round_date_time(datetime.now() + timedelta(hours=1)),
        end=BookingSlot.round_date_time(datetime.now() + timedelta(hours=3)),
    )
    assert slot.customer_count == 0


@pytest.mark.django_db
def test_customer_list(walk_service, make_pet):
    pet = make_pet()
    booking = Booking.objects.create(
        cost=0,
        start=BookingSlot.round_date_time(datetime.now() + timedelta(hours=5)),
        end=BookingSlot.round_date_time(datetime.now() + timedelta(hours=6)),
        service=walk_service,
        pet=pet,
    )

    assert pet.customer in booking.booking_slot.customers


@pytest.mark.django_db
def test_pet_list(walk_service, make_pet):
    pet = make_pet()
    booking = Booking.objects.create(
        cost=0,
        start=BookingSlot.round_date_time(datetime.now() + timedelta(hours=5)),
        end=BookingSlot.round_date_time(datetime.now() + timedelta(hours=6)),
        service=walk_service,
        pet=pet,
    )

    assert pet in booking.booking_slot.pets


class BookingSlotCreation(TestCase):
    def setUp(self) -> None:
        self.walk_service = Service.objects.create(
            name="Walk", length=timedelta(minutes=60), booked_length=timedelta(minutes=120), cost=12, max_pet=4, max_customer=1
        )

        self.customer = Customer.objects.create(name="Test Customer")

        self.pet0 = Pet.objects.create(name="Test Pet 0", customer=self.customer)
        self.pet1 = Pet.objects.create(name="Test Pet 1", customer=self.customer)
        self.pet2 = Pet.objects.create(name="Test Pet 2", customer=self.customer)
        self.pet3 = Pet.objects.create(name="Test Pet 3", customer=self.customer)
        self.pet4 = Pet.objects.create(name="Test Pet 4", customer=self.customer)

        self.now = datetime.now()

    def create_booking(self, start_offset=5, end_offset=6, **kwargs) -> Booking:
        args = {
            **{
                "cost": 0,
                "start": BookingSlot.round_date_time(self.now + timedelta(hours=start_offset)),
                "end": BookingSlot.round_date_time(self.now + timedelta(hours=end_offset)),
                "service": self.walk_service,
                "pet": self.pet1,
            },
            **kwargs,
        }

        return Booking.objects.create(**args)

    def test_max_pet_booking(self):
        for i in range(4):
            booking = self.create_booking(pet=getattr(self, f"pet{i}"))
            booking.save()

        with self.assertRaises(BookingSlotMaxPets):
            self.create_booking(pet=self.pet4)

    def test_max_customer_booking(self):
        for i in range(2):
            booking = self.create_booking(pet=getattr(self, f"pet{i}"))
            booking.save()

        customer = Customer.objects.create(name="test customer 2")

        pet = Pet.objects.create(name="Test Pet customer 2", customer=customer)

        with self.assertRaises(BookingSlotMaxCustomers):
            self.create_booking(pet=pet)


class test_booking_states(TestCase):
    def setUp(self) -> None:
        # self.service = baker.make(Service, name="Test Service")

        return super().setUp()

    def test_transitions(self):
        booking = Booking()
        transitions = list(booking.get_all_state_transitions())

        valid_transitions = [
            ("enquiry", "canceled"),
            ("preliminary", "canceled"),
            ("confirmed", "canceled"),
            ("confirmed", "completed"),
            ("preliminary", "confirmed"),
            ("enquiry", "preliminary"),
            ("canceled", "enquiry"),
        ]

        for t in transitions:
            self.assertIn((t.source, t.target), valid_transitions)

        self.assertEqual(len(valid_transitions), len(transitions))

    def test_complete(self):
        booking: Booking = baker.make(Booking)
        booking.save()
        booking.confirm()

        before_count = len(Charge.objects.all())
        booking.complete()

        charges = Charge.objects.all().reverse()
        self.assertEqual(len(charges), before_count + 1)

        charge = charges[0]

        self.assertEqual(booking, charge.booking)
        self.assertEqual(booking.pet.customer, charge.customer)
        self.assertEqual(booking.cost, charge.cost)
