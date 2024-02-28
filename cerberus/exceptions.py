class BookingSlotError(Exception):
    pass


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
