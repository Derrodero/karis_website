from django.contrib import admin

from clinic.models import Appointment, AppointmentSlot, Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(AppointmentSlot)
class AppointmentSlotAdmin(admin.ModelAdmin):
    list_display = ("service", "starts_at", "ends_at", "is_active", "is_booked")
    list_filter = ("is_active", "service")
    date_hierarchy = "starts_at"
    ordering = ("starts_at",)

    @admin.display(boolean=True, description="Booked")
    def is_booked(self, slot: AppointmentSlot) -> bool:
        return slot.appointments.filter(status=Appointment.Status.CONFIRMED).exists()


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "full_name",
        "branch",
        "specialty",
        "slot",
        "status",
        "created_at",
    )
    list_filter = ("status", "branch", "slot__service")
    search_fields = ("full_name", "email", "phone", "reference")
    readonly_fields = (
        "reference",
        "branch",
        "slot",
        "full_name",
        "phone",
        "email",
        "specialty",
        "notes",
        "consented_at",
        "created_at",
    )
    fields = readonly_fields + ("status",)
    date_hierarchy = "created_at"
    actions = None

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.site_header = "Karis Medical staff"
admin.site.site_title = "Karis Medical staff"
admin.site.index_title = "Appointment scheduling"
