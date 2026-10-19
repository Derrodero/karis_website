from django import forms
from django.core.validators import RegexValidator
from django.utils import timezone

from clinic.models import Appointment, AppointmentSlot, Service


class AppointmentSlotSelect(forms.Select):
    def __init__(self, service_by_slot: dict[str, str], *args, **kwargs):
        self.service_by_slot = service_by_slot
        super().__init__(*args, **kwargs)

    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        option = super().create_option(
            name, value, label, selected, index, subindex, attrs
        )
        service_id = self.service_by_slot.get(str(value))
        if service_id and option["attrs"] is not None:
            option["attrs"]["data-service"] = service_id
        return option


class AppointmentForm(forms.Form):
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
    slot = forms.ModelChoiceField(
        label="Available date and time",
        queryset=AppointmentSlot.objects.none(),
        empty_label="Choose an available time",
    )
    consent = forms.BooleanField(
        label="I agree that Karis Medical may use these details to manage this appointment.",
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        services = Service.objects.filter(is_active=True)
        slots = list(
            AppointmentSlot.objects.select_related("service")
            .filter(
                is_active=True,
                starts_at__gt=timezone.now(),
                service__is_active=True,
            )
            .exclude(appointments__status=Appointment.Status.CONFIRMED)
            .order_by("starts_at")
        )
        self.fields["service"].queryset = services
        self.fields["slot"].queryset = AppointmentSlot.objects.filter(
            pk__in=[slot.pk for slot in slots]
        ).select_related("service")
        self.fields["slot"].widget = AppointmentSlotSelect(
            {str(slot.pk): str(slot.service_id) for slot in slots}
        )
        self.fields["slot"].widget.choices = self.fields["slot"].choices

    def clean(self):
        cleaned_data = super().clean()
        service = cleaned_data.get("service")
        slot = cleaned_data.get("slot")
        if service and slot and slot.service_id != service.pk:
            self.add_error("slot", "Choose a time listed for the selected service.")
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
        widget=forms.TimeInput(attrs={"type": "time", "step": "900"}),
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
            from datetime import datetime, timedelta

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
