from datetime import datetime, timedelta

from django import forms
from django.core.validators import RegexValidator
from django.utils import timezone

from clinic.content import BRANCHES, SPECIALTY_FILTERS
from clinic.models import Appointment, AppointmentSlot, Service

APPOINTMENT_TIMES = ("09:00", "10:30", "12:00", "14:00", "15:30")
APPOINTMENT_TIME_CHOICES = (
    ("09:00", "9:00 AM"),
    ("10:30", "10:30 AM"),
    ("12:00", "12:00 PM"),
    ("14:00", "2:00 PM"),
    ("15:30", "3:30 PM"),
)


class AppointmentSlotSelect(forms.Select):
    def __init__(self, slot_metadata: dict[str, dict[str, str]], *args, **kwargs):
        self.slot_metadata = slot_metadata
        super().__init__(*args, **kwargs)

    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        metadata = self.slot_metadata.get(str(value))
        if metadata:
            label = f"{metadata['date_label']} at {metadata['time_label']}"
        option = super().create_option(
            name, value, label, selected, index, subindex, attrs
        )
        if metadata and option["attrs"] is not None:
            option["attrs"].update(
                {
                    "data-service": metadata["service"],
                    "data-date": metadata["date"],
                    "data-time": metadata["time"],
                }
            )
        return option


class AppointmentForm(forms.Form):
    branch = forms.ChoiceField(
        label="Clinic location",
        choices=tuple((branch["key"], branch["name"]) for branch in BRANCHES),
    )
    full_name = forms.CharField(
        label="Full name",
        max_length=120,
        widget=forms.TextInput(attrs={"autocomplete": "name"}),
    )
    phone = forms.CharField(
        label="Phone",
        max_length=32,
        validators=[
            RegexValidator(
                regex=r"^\+?[0-9\s().-]{7,31}$",
                message="Enter a phone number using digits and common phone punctuation.",
            )
        ],
        widget=forms.TextInput(attrs={"type": "tel", "autocomplete": "tel"}),
    )
    email = forms.EmailField(
        label="Email",
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )
    service = forms.ModelChoiceField(
        label="Service",
        queryset=Service.objects.none(),
        empty_label="Choose a service",
    )
    specialty = forms.ChoiceField(
        label="Specialty or care area (optional)",
        choices=(("", "Choose a care area"),)
        + tuple((label, label) for _, label in SPECIALTY_FILTERS),
        required=False,
    )
    slot = forms.ModelChoiceField(
        label="Available date and time",
        queryset=AppointmentSlot.objects.none(),
        empty_label="Choose an available time",
    )
    date = forms.DateField(
        label="Appointment date",
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "min": timezone.localdate().isoformat(),
                "data-appointment-date": "",
            }
        ),
    )
    notes = forms.CharField(
        label="Additional notes (optional)",
        required=False,
        max_length=500,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": "Share practical appointment details only.",
            }
        ),
        help_text="Do not include symptoms, diagnoses, or medical history.",
    )
    consent = forms.BooleanField(
        label="I agree that Karis Medical may use these details to manage this appointment.",
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["date"].widget.attrs["min"] = timezone.localdate().isoformat()
        services = Service.objects.filter(is_active=True)
        available_slots = list(
            AppointmentSlot.objects.select_related("service")
            .filter(
                is_active=True,
                starts_at__gt=timezone.now(),
                service__is_active=True,
            )
            .exclude(appointments__status=Appointment.Status.CONFIRMED)
            .order_by("starts_at")
        )
        slots = [
            slot
            for slot in available_slots
            if timezone.localtime(slot.starts_at).strftime("%H:%M")
            in APPOINTMENT_TIMES
        ]
        self.fields["service"].queryset = services
        self.fields["slot"].queryset = AppointmentSlot.objects.filter(
            pk__in=[slot.pk for slot in slots]
        ).select_related("service")
        self.fields["slot"].widget = AppointmentSlotSelect(
            {
                str(slot.pk): {
                    "service": str(slot.service_id),
                    "date": timezone.localtime(slot.starts_at).date().isoformat(),
                    "time": timezone.localtime(slot.starts_at).strftime("%H:%M"),
                    "date_label": timezone.localtime(slot.starts_at).strftime(
                        "%A, %d %B %Y"
                    ),
                    "time_label": timezone.localtime(slot.starts_at).strftime(
                        "%I:%M %p"
                    ).lstrip("0"),
                }
                for slot in slots
            }
        )
        self.fields["slot"].widget.choices = self.fields["slot"].choices

    def clean(self):
        cleaned_data = super().clean()
        service = cleaned_data.get("service")
        slot = cleaned_data.get("slot")
        appointment_date = cleaned_data.get("date")
        if service and slot and slot.service_id != service.pk:
            self.add_error("slot", "Choose a time listed for the selected service.")
        if appointment_date and appointment_date < timezone.localdate():
            self.add_error("date", "Choose today or a future date.")
        if appointment_date and slot:
            slot_date = timezone.localtime(slot.starts_at).date()
            if slot_date != appointment_date:
                self.add_error("slot", "Choose an available time on the selected date.")
        return cleaned_data


class StaffSlotForm(forms.Form):
    service = forms.ModelChoiceField(
        label="Service",
        queryset=Service.objects.none(),
        empty_label="Select service",
    )
    date = forms.DateField(
        label="Date",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    start_time = forms.TimeField(
        label="Start time",
        widget=forms.Select(choices=APPOINTMENT_TIME_CHOICES),
    )
    duration_minutes = forms.ChoiceField(
        label="Duration",
        choices=(
            ("30", "30 minutes"),
            ("45", "45 minutes"),
            ("60", "60 minutes"),
        ),
        initial="30",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service"].queryset = Service.objects.filter(is_active=True)
        if not self.is_bound:
            self.fields["date"].initial = timezone.localdate()

    def clean(self):
        cleaned_data = super().clean()
        slot_date = cleaned_data.get("date")
        start_time = cleaned_data.get("start_time")
        duration = int(cleaned_data.get("duration_minutes") or 30)
        if slot_date and start_time:
            naive_start = datetime.combine(slot_date, start_time)
            starts_at = timezone.make_aware(
                naive_start, timezone.get_current_timezone()
            )
            if starts_at <= timezone.now():
                self.add_error("start_time", "Slot start time must be in the future.")
            cleaned_data["starts_at"] = starts_at
            cleaned_data["ends_at"] = starts_at + timedelta(minutes=duration)
        return cleaned_data


class StaffBulkSlotForm(forms.Form):
    services = forms.ModelMultipleChoiceField(
        label="Services",
        queryset=Service.objects.none(),
        widget=forms.CheckboxSelectMultiple,
    )
    start_date = forms.DateField(
        label="Start date",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    days = forms.IntegerField(
        label="Number of days",
        min_value=1,
        max_value=14,
        initial=7,
    )
    day_start = forms.TimeField(
        label="Daily start time",
        initial="09:00",
        widget=forms.TimeInput(attrs={"type": "time", "step": "1800"}),
    )
    day_end = forms.TimeField(
        label="Daily end time",
        initial="17:00",
        widget=forms.TimeInput(attrs={"type": "time", "step": "1800"}),
    )
    duration_minutes = forms.ChoiceField(
        label="Slot duration",
        choices=(
            ("30", "30 minutes"),
            ("60", "60 minutes"),
        ),
        initial="60",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        active_services = Service.objects.filter(is_active=True)
        self.fields["services"].queryset = active_services
        if not self.is_bound:
            from datetime import timedelta

            self.fields["start_date"].initial = timezone.localdate() + timedelta(days=1)
            self.fields["services"].initial = list(
                active_services.values_list("pk", flat=True)
            )

    def clean(self):
        cleaned_data = super().clean()
        day_start = cleaned_data.get("day_start")
        day_end = cleaned_data.get("day_end")
        if day_start and day_end and day_end <= day_start:
            self.add_error("day_end", "End time must be after start time.")
        return cleaned_data
