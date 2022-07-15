# Django
from django.contrib import admin

# Locals
from .models import Address, Booking, BookingSlot, Charge, Contact, Customer, Invoice, InvoiceOpen, Pet, Service, Vet


@admin.action(description="Mark selected inactive")
def make_inactive(modeladmin, request, queryset):
    queryset.update(active=False)


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
    list_display = ("active", "name", "created")
    actions = (make_inactive,)


class PetAdmin(admin.ModelAdmin):
    list_display = ("active", "name", "created")
    actions = (make_inactive,)


class VetAdmin(admin.ModelAdmin):
    pass


class InvoiceAdmin(admin.ModelAdmin):
    readonly_fields = ["state"]


class InvoiceOpenAdmin(admin.ModelAdmin):
    list_display = ("invoice", "opened")


admin.site.register(Customer, CustomerAdmin)
admin.site.register(Pet, PetAdmin)
admin.site.register(Vet, VetAdmin)
admin.site.register(Address, AddressAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(Booking, BookingAdmin)
admin.site.register(BookingSlot, BookingSlotAdmin)
admin.site.register(Charge, ChargeAdmin)
admin.site.register(Contact, ContactAdmin)
admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(InvoiceOpen, InvoiceOpenAdmin)
