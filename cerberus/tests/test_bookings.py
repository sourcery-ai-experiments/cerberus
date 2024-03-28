# Standard Library
from collections.abc import Callable, Generator
from datetime import datetime, timedelta
from functools import partial

# Django
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

# Third Party
import pytest
from model_bakery import baker

# Locals
from ..exceptions import MaxCustomersError, MaxPetsError
from ..models import Booking, BookingSlot, Charge, Customer, Pet, Service


@pytest.fixture
def walk_service() -> Generator[Service, None, None]:
    yield baker.make(Service, max_pet=4, max_customer=2)


@pytest.fixture
def customer() -> Generator[Customer, None, None]:
    yield baker.make(Customer)


@pytest.fixture
def make_pet(customer: Customer) -> Generator[Callable[[], Pet], None, None]:
    yield partial(baker.make, Pet, customer=customer)


@pytest.fixture
def booking() -> Generator[Booking, None, None]:
    yield baker.make(Booking)


@pytest.fixture
def now() -> Generator[datetime, None, None]:
    yield datetime.now()


@pytest.mark.django_db
def test_end_before_start():
    booking_slot = baker.make(BookingSlot)

    booking_slot.start = BookingSlot.round_date_time(datetime.now() + timedelta(hours=2))
    booking_slot.end = BookingSlot.round_date_time(datetime.now() + timedelta(hours=1))

    with pytest.raises(IntegrityError):
        booking_slot.save()


@pytest.mark.django_db
@pytest.mark.freeze_time("2017-05-21")
def test_has_overlap():
    baker.make(
        Booking,
        start=BookingSlot.round_date_time(datetime.now() + timedelta(hours=1)),
        end=BookingSlot.round_date_time(datetime.now() + timedelta(hours=3)),
        _booking_slot=None,
    )

    slot = baker.make(
        BookingSlot,
        start=BookingSlot.round_date_time(datetime.now() + timedelta(hours=2)),
        end=BookingSlot.round_date_time(datetime.now() + timedelta(hours=4)),
    )

    assert slot.overlaps() is True


@pytest.mark.django_db
def test_does_not_have_overlap(walk_service, make_pet):
    baker.make(
        Booking,
        start=BookingSlot.round_date_time(datetime.now() + timedelta(hours=2)),
        end=BookingSlot.round_date_time(datetime.now() + timedelta(hours=3)),
        _booking_slot=None,
    )

    slot = baker.make(
        BookingSlot,
        start=BookingSlot.round_date_time(datetime.now() + timedelta(hours=5)),
        end=BookingSlot.round_date_time(datetime.now() + timedelta(hours=6)),
    )

    assert slot.overlaps() is False


@pytest.mark.django_db
def test_get_existing_slot():
    slot = baker.make(
        BookingSlot,
        start=BookingSlot.round_date_time(datetime.now() + timedelta(hours=1)),
        end=BookingSlot.round_date_time(datetime.now() + timedelta(hours=3)),
    )
    same_slot = BookingSlot.get_slot(start=slot.start, end=slot.end)

    assert same_slot.id == slot.id


@pytest.mark.django_db
def test_no_duplicates():
    slot = baker.make(
        BookingSlot,
        start=BookingSlot.round_date_time(datetime.now() + timedelta(hours=1)),
        end=BookingSlot.round_date_time(datetime.now() + timedelta(hours=3)),
    )

    with pytest.raises(IntegrityError):
        empty_slot = BookingSlot(start=slot.start, end=slot.end)
        empty_slot.save()


@pytest.mark.django_db
def test_pet_count(walk_service, make_pet):
    booking_slot_1 = baker.make(
        Booking,
        start=BookingSlot.round_date_time(datetime.now() + timedelta(hours=5)),
        end=BookingSlot.round_date_time(datetime.now() + timedelta(hours=6)),
        booking_slot=None,
        service=walk_service,
        pets=[make_pet()],
    ).booking_slot

    booking_slot_2 = baker.make(
        Booking,
        start=BookingSlot.round_date_time(datetime.now() + timedelta(hours=5)),
        end=BookingSlot.round_date_time(datetime.now() + timedelta(hours=6)),
        booking_slot=None,
        service=walk_service,
        pets=[make_pet()],
    ).booking_slot

    assert booking_slot_1.pk == booking_slot_2.pk
    assert booking_slot_1.pet_count == 2


@pytest.mark.django_db
def test_customer_count(walk_service):
    booking_slot_1 = baker.make(
        Booking,
        start=BookingSlot.round_date_time(datetime.now() + timedelta(hours=5)),
        end=BookingSlot.round_date_time(datetime.now() + timedelta(hours=6)),
        service=walk_service,
        booking_slot=None,
        customer=baker.make(Customer),
    ).booking_slot

    booking_slot_2 = baker.make(
        Booking,
        start=BookingSlot.round_date_time(datetime.now() + timedelta(hours=5)),
        end=BookingSlot.round_date_time(datetime.now() + timedelta(hours=6)),
        service=walk_service,
        booking_slot=None,
        customer=baker.make(Customer),
    ).booking_slot

    assert booking_slot_1.pk == booking_slot_2.pk
    assert booking_slot_1.customer_count == 2


@pytest.mark.django_db
def test_no_pet_count():
    slot = baker.make(
        BookingSlot,
        start=BookingSlot.round_date_time(datetime.now() + timedelta(hours=1)),
        end=BookingSlot.round_date_time(datetime.now() + timedelta(hours=3)),
    )
    assert slot.pet_count == 0


@pytest.mark.django_db
def test_no_customer_count():
    slot = baker.make(
        BookingSlot,
        start=BookingSlot.round_date_time(datetime.now() + timedelta(hours=1)),
        end=BookingSlot.round_date_time(datetime.now() + timedelta(hours=3)),
    )
    assert slot.customer_count == 0


@pytest.mark.django_db
def test_customer_list(make_pet, customer):
    pet = make_pet(customer=customer)
    booking = baker.make(
        Booking,
        start=BookingSlot.round_date_time(datetime.now() + timedelta(hours=5)),
        end=BookingSlot.round_date_time(datetime.now() + timedelta(hours=6)),
        pets=[pet],
        customer=customer,
    )

    assert pet.customer in booking.booking_slot.customers


@pytest.mark.django_db
def test_pet_list(make_pet):
    pet = make_pet()
    booking = baker.make(
        Booking,
        start=BookingSlot.round_date_time(datetime.now() + timedelta(hours=5)),
        end=BookingSlot.round_date_time(datetime.now() + timedelta(hours=6)),
        pets=[pet],
    )

    assert pet in booking.booking_slot.pets


@pytest.mark.django_db
@pytest.mark.freeze_time("2017-05-21")
def test_max_pet_booking(walk_service, now):
    customer = baker.make(Customer)

    start = BookingSlot.round_date_time(now + timedelta(hours=1))
    end = BookingSlot.round_date_time(now + timedelta(hours=2))

    pets = [baker.make(Pet, customer=customer) for _ in range(4)]

    baker.make(Booking, pets=pets, customer=customer, service=walk_service, start=start, end=end)

    with pytest.raises(MaxPetsError):
        baker.make(Booking, pets=[baker.make(Pet, customer=customer)], service=walk_service, start=start, end=end)


@pytest.mark.django_db
@pytest.mark.freeze_time("2017-05-21")
def test_max_customer_booking(now, walk_service):
    c1 = baker.make(Customer)
    c2 = baker.make(Customer)
    c3 = baker.make(Customer)

    def pet(c):
        return baker.make(Pet, customer=c)

    start = BookingSlot.round_date_time(now + timedelta(hours=1))
    end = BookingSlot.round_date_time(now + timedelta(hours=2))

    baker.make(Booking, pets=[pet(c1)], customer=c1, service=walk_service, start=start, end=end)
    baker.make(Booking, pets=[pet(c2)], customer=c2, service=walk_service, start=start, end=end)

    with pytest.raises(MaxCustomersError):
        baker.make(Booking, pets=[pet(c3)], customer=c3, service=walk_service, start=start, end=end)


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
    assert booking.customer == charge.customer
    assert booking.cost == charge.amount


@pytest.mark.django_db
def test_booking_start_before_end():
    booking = baker.make(Booking)

    booking.start = BookingSlot.round_date_time(datetime.now() + timedelta(hours=2))
    booking.end = BookingSlot.round_date_time(datetime.now() + timedelta(hours=1))

    with pytest.raises(IntegrityError):
        booking.save()


@pytest.mark.django_db
def test_booking_requires_slot():
    booking = baker.make(Booking)
    booking.booking_slot = None

    with pytest.raises(IntegrityError):
        booking.save()


@pytest.mark.django_db
def test_booking_canceled_requires_no_slot():
    booking = baker.make(Booking)
    booking.cancel()
    booking.booking_slot = booking._get_new_booking_slot()

    with pytest.raises(IntegrityError):
        booking.save()


@pytest.mark.django_db
def test_booking_pets_and_customers_match(walk_service):
    pet = baker.make(Pet)
    booking = baker.prepare(Booking, pets=[pet], service=walk_service)
    booking.customer = pet.customer
    booking.save()

    assert booking.customer == pet.customer


@pytest.mark.django_db
def test_booking_pets_and_customers_mismatch(customer, walk_service):
    pet = baker.make(Pet)
    booking = baker.prepare(Booking, pets=[pet], service=walk_service)
    booking.customer = customer
    booking.save()

    with pytest.raises(ValidationError):
        booking.clean()
