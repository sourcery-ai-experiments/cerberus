# Django
from django.contrib import admin

# Locals
from .models import (
    Address,
    Booking,
    BookingSlot,
    Charge,
    Contact,
    Customer,
    Invoice,
    InvoiceOpen,
    Payment,
    Pet,
    Service,
    UserSettings,
    Vet,
)


@admin.action(description="Mark selected inactive")
def make_inactive(modeladmin, request, queryset):
    queryset.update(active=False)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    pass


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    pass


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    readonly_fields = ["state"]


@admin.register(BookingSlot)
class BookingSlotAdmin(admin.ModelAdmin):
    pass


@admin.register(Charge)
class ChargeAdmin(admin.ModelAdmin):
    readonly_fields = ["state"]


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    pass


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("active", "first_name", "last_name", "created")
    actions = (make_inactive,)


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ("active", "name", "created")
    actions = (make_inactive,)


@admin.register(Vet)
class VetAdmin(admin.ModelAdmin):
    pass


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    readonly_fields = ["state"]


@admin.register(InvoiceOpen)
class InvoiceOpenAdmin(admin.ModelAdmin):
    list_display = ("invoice", "opened")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    pass


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    pass
