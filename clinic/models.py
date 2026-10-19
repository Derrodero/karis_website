import uuid

from django.core.validators import RegexValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class Service(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.CharField(max_length=500, blank=True)
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class AppointmentSlot(models.Model):
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name="slots")
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["starts_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["service", "starts_at"], name="unique_service_slot_start"
            ),
            models.CheckConstraint(
                condition=Q(ends_at__gt=F("starts_at")), name="slot_end_after_start"
            ),
        ]

    def __str__(self) -> str:
        start = timezone.localtime(self.starts_at)
        return f"{self.service.name} - {start:%a, %d %b %Y %H:%M}"

    @property
    def display_time(self) -> str:
        return timezone.localtime(self.starts_at).strftime("%A, %d %B %Y, %H:%M")


class Appointment(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    slot = models.ForeignKey(
        AppointmentSlot, on_delete=models.PROTECT, related_name="appointments"
    )
    full_name = models.CharField(max_length=120)
    phone = models.CharField(
        max_length=32,
        validators=[
            RegexValidator(
                regex=r"^\+?[0-9\s().-]{7,31}$",
                message="Enter a phone number using digits and common phone punctuation.",
            )
        ],
    )
    email = models.EmailField(max_length=254)
    consented_at = models.DateTimeField()
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.CONFIRMED
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["slot"],
                condition=Q(status="confirmed"),
                name="one_confirmed_appointment_per_slot",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.reference} - {self.slot}"
