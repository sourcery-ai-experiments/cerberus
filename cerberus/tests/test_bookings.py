# Standard Library
from collections.abc import Callable, Generator
from datetime import datetime, timedelta
from functools import partial

# Django
from django.db.utils import IntegrityError

# Third Party
import pytest
from model_bakery import baker

# Locals
from ..exceptions import BookingSlotMaxCustomers, BookingSlotMaxPets
from ..models import Booking, BookingSlot, Charge, Customer, Pet, Service


@pytest.fixture
def walk_service() -> Generator[Service, None, None]:
    yield baker.make(Service, max_pet=4, max_customer=1)


@pytest.fixture
def customer() -> Generator[Customer, None, None]:
    yield baker.make(Customer)


@pytest.fixture
def make_pet(customer: Customer) -> Generator[Callable[[], Pet], None, None]:
    yield partial(baker.make, Pet, customer=customer)


@pytest.fixture
def booking() -> Generator[Booking, None, None]:
    yield baker.make(Booking)


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


@pytest.fixture
def now() -> Generator[datetime, None, None]:
    yield datetime.now()


@pytest.fixture
def make_booking(make_pet, walk_service, now) -> Generator[Callable[[Pet | None], Booking], None, None]:
    def _make_booking(pet: Pet | None = None):
        booking = Booking.objects.create(
            cost=0,
            pet=pet or make_pet(),
            service=walk_service,
            start=BookingSlot.round_date_time(now + timedelta(hours=1)),
            end=BookingSlot.round_date_time(now + timedelta(hours=2)),
        )
        booking.save()
        return booking

    yield _make_booking


@pytest.mark.django_db
@pytest.mark.freeze_time("2017-05-21")
def test_max_pet_booking(make_booking):
    for _ in range(4):
        make_booking()

    with pytest.raises(BookingSlotMaxPets):
        make_booking()


@pytest.mark.django_db
@pytest.mark.freeze_time("2017-05-21")
def test_max_customer_booking(make_booking):
    for i in range(2):
        make_booking()

    with pytest.raises(BookingSlotMaxCustomers):
        make_booking(pet=baker.make(Pet))


@pytest.mark.django_db
def test_transitions(booking):
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

    assert all((t.source, t.target) in valid_transitions for t in transitions)
    assert len(valid_transitions) == len(transitions)


@pytest.mark.django_db
def test_complete():
    booking: Booking = baker.make(Booking)
    booking.save()
    booking.confirm()

    before_count = len(Charge.objects.all())
    booking.complete()

    charges = Charge.objects.all().reverse()
    assert len(charges) == before_count + 1

    charge = charges[0]

    assert booking == charge.booking
    assert booking.pet.customer == charge.customer
    assert booking.cost == charge.cost
