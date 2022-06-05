# Django
from django.contrib import admin

# Locals
from .models import Address, Booking, BookingSlot, Charge, Contact, Customer, Pet, Service, Vet


class AddressAdmin(admin.ModelAdmin):
    pass


class ServiceAdmin(admin.ModelAdmin):
    pass


class BookingAdmin(admin.ModelAdmin):
    readonly_fields = ["state"]


class BookingSlotAdmin(admin.ModelAdmin):
    pass


class ChargeAdmin(admin.ModelAdmin):
    readonly_fields = ["state"]


class ContactAdmin(admin.ModelAdmin):
    pass


class CustomerAdmin(admin.ModelAdmin):
    pass


class PetAdmin(admin.ModelAdmin):
    pass


class VetAdmin(admin.ModelAdmin):
    pass


admin.site.register(Customer, CustomerAdmin)
admin.site.register(Pet, PetAdmin)
admin.site.register(Vet, VetAdmin)
admin.site.register(Address, AddressAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(Booking, BookingAdmin)
admin.site.register(BookingSlot, BookingSlotAdmin)
admin.site.register(Charge, ChargeAdmin)
admin.site.register(Contact, ContactAdmin)
