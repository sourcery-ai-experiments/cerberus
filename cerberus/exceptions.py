class BookingSlotException(Exception):
    pass


class BookingSlotIncorectService(BookingSlotException):
    pass


class BookingSlotMaxCustomers(BookingSlotException):
    pass


class BookingSlotMaxPets(BookingSlotException):
    pass


class BookingSlotOverlaps(BookingSlotException):
    pass


class InvalidEmail(Exception):
    pass
