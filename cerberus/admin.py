# Django
from django.contrib import admin

# Third Party
from fsm_admin2.admin import FSMTransitionMixin

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


class PetInline(admin.StackedInline):
    model = Pet
    extra = 1


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "created", "active")
    actions = (make_inactive,)
    inlines = [PetInline]


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ("active", "name", "created")
    actions = (make_inactive,)


@admin.register(Vet)
class VetAdmin(admin.ModelAdmin):
    pass


class ChargeInline(admin.TabularInline):
    model = Charge
    extra = 3

    readonly_fields = ["state", "paid_on", "customer"]


@admin.register(Invoice)
class InvoiceAdmin(FSMTransitionMixin, admin.ModelAdmin):
    fsm_fields = ["state"]  # list your fsm fields
    readonly_fields = ["state", "paid_on", "sent_on"]
    list_display = ("name", "customer", "state", "total", "due", "paid_on", "sent_on")

    inlines = [ChargeInline]
    list_filter = ["state", "customer"]


@admin.register(InvoiceOpen)
class InvoiceOpenAdmin(admin.ModelAdmin):
    list_display = ("invoice", "opened")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("amount", "invoice", "created")


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    pass
