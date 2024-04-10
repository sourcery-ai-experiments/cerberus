# Third Party
from rest_framework import status
from rest_framework.exceptions import APIException


class BookingSlotError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST


class IncorectServiceError(BookingSlotError):
    pass


class MaxCustomersError(BookingSlotError):
    pass


class MaxPetsError(BookingSlotError):
    pass


class SlotOverlapsError(BookingSlotError):
    pass


class InvalidEmailError(Exception):
    pass


class ChargeRefundError(Exception):
    pass
