import logging
from datetime import datetime, time, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from clinic.content import (
    ABOUT_PROFILE,
    BRANCHES,
    DOCTOR_PROFILES,
    EXECUTIVE_TEAM,
    FOUNDER,
    INSURERS,
    OPENING_HOURS,
    PAGES,
    PUBLIC_FACTS,
    SERVICE_GROUPS,
    SERVICE_REFERENCE,
    SERVICE_REFERENCE_NOTE,
    SPECIALTY_FILTERS,
)
from clinic.forms import (
    APPOINTMENT_TIMES,
    AppointmentForm,
    StaffBulkSlotForm,
    StaffSlotForm,
)
from clinic.models import Appointment, AppointmentSlot, Service

logger = logging.getLogger(__name__)


def _is_staff_user(user) -> bool:
    return bool(user and user.is_authenticated and user.is_staff)


def _render_page(
    request: HttpRequest, page_key: str, extra_context=None
) -> HttpResponse:
    context = {
        "page": PAGES[page_key],
        "page_key": page_key,
        "page_title": f"{PAGES[page_key]['title']} | Karis Medical",
        "facts": PUBLIC_FACTS,
        "branches": BRANCHES,
        "opening_hours": OPENING_HOURS,
        "show_branches": page_key == "contact",
    }
    if extra_context:
        context.update(extra_context)
    return render(
        request,
        "clinic/information_page.html",
        context,
    )


def home(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "clinic/home.html",
        {
            "page_title": "Karis Medical | Uganda",
            "appointment_cta": (
                "Book an appointment"
                if settings.APPOINTMENTS_ENABLED
                else "Appointment information"
            ),
            "branches": BRANCHES,
            "opening_hours": OPENING_HOURS,
            "facts": PUBLIC_FACTS,
        },
    )


def about(request: HttpRequest) -> HttpResponse:
    return _render_page(
        request,
        "about",
        {
            "about": ABOUT_PROFILE,
            "services": Service.objects.filter(is_active=True),
            "show_branches": True,
        },
    )


def about_detail(request: HttpRequest, slug: str) -> HttpResponse:
    team_member = next(
        (
            member
            for member in [FOUNDER, *EXECUTIVE_TEAM]
            if member["slug"] == slug
        ),
        None,
    )
    if team_member is not None:
        return render(
            request,
            "clinic/team_profile.html",
            {
                "page_title": f"{team_member['name']} | Karis Medical",
                "facts": PUBLIC_FACTS,
                "team_member": team_member,
            },
        )

    detail_pages = [
        *ABOUT_PROFILE["team_roles"],
        ABOUT_PROFILE["future_development"],
    ]
    detail = next((item for item in detail_pages if item["slug"] == slug), None)
    if detail is None:
        raise Http404("About detail page not found.")

    if detail["slug"] == "medical-team":
        team_members = [
            {
                **member,
                "profile_url": reverse("about_detail", args=[member["slug"]]),
            }
            for member in [FOUNDER, *EXECUTIVE_TEAM]
        ]
        return render(
            request,
            "clinic/medical_team.html",
            {
                "page_title": "Founder and Executive Team | Karis Medical",
                "facts": PUBLIC_FACTS,
                "detail": detail,
                "team_members": team_members,
            },
        )

    return render(
        request,
        "clinic/about_detail.html",
        {
            "page_title": f"{detail['title']} | Karis Medical",
            "facts": PUBLIC_FACTS,
            "detail": detail,
            "about": ABOUT_PROFILE,
            "detail_section": (
                "Looking ahead"
                if detail["slug"] == ABOUT_PROFILE["future_development"]["slug"]
                else "Medical team and leadership"
            ),
        },
    )


def find_doctor(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "clinic/find_doctor.html",
        {
            "page_title": "Find a Doctor | Karis Medical",
            "facts": PUBLIC_FACTS,
            "doctors": DOCTOR_PROFILES,
            "specialty_filters": SPECIALTY_FILTERS,
            "branches": BRANCHES,
        },
    )


def doctor_profile(request: HttpRequest, slug: str) -> HttpResponse:
    doctor = next(
        (profile for profile in DOCTOR_PROFILES if profile["slug"] == slug),
        None,
    )
    if doctor is None:
        raise Http404("Doctor profile not found.")

    return render(
        request,
        "clinic/doctor_profile.html",
        {
            "page_title": f"{doctor['specialty']} Profile | Karis Medical",
            "facts": PUBLIC_FACTS,
            "doctor": doctor,
        },
    )


def _process_appointment_booking(
    request: HttpRequest, redirect_route: str = "appointments"
) -> tuple[dict, HttpResponse | None]:
    context: dict = {
        "appointments_enabled": settings.APPOINTMENTS_ENABLED,
        "retention_days": settings.APPOINTMENT_RETENTION_DAYS,
    }
    if not settings.APPOINTMENTS_ENABLED:
        context["form"] = None
        return context, None

    reference = request.session.pop("appointment_reference", None)
    email_warning = request.session.pop("appointment_email_warning", False)
    if reference:
        booking = (
            Appointment.objects.select_related("slot__service")
            .filter(reference=reference)
            .first()
        )
        if booking:
            context.update(
                {
                    "booking": booking,
                    "booking_time": booking.slot.display_time,
                    "email_warning": email_warning,
                    "form": None,
                }
            )
            return context, None

    form = AppointmentForm(request.POST or None)
    if not form.is_bound:
        preselected_service = request.GET.get("service", "")
        if preselected_service.isdigit():
            form.fields["service"].initial = int(preselected_service)
        preselected_specialty = request.GET.get("specialty", "")
        if preselected_specialty in {
            label for _, label in SPECIALTY_FILTERS
        }:
            form.fields["specialty"].initial = preselected_specialty

    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                slot = AppointmentSlot.objects.select_for_update().get(
                    pk=form.cleaned_data["slot"].pk,
                    service=form.cleaned_data["service"],
                    is_active=True,
                    starts_at__gt=timezone.now(),
                    service__is_active=True,
                )
                if slot.appointments.filter(
                    status=Appointment.Status.CONFIRMED
                ).exists():
                    raise AppointmentSlot.DoesNotExist
                booking = Appointment.objects.create(
                    slot=slot,
                    full_name=form.cleaned_data["full_name"],
                    phone=form.cleaned_data["phone"],
                    email=form.cleaned_data["email"],
                    specialty=form.cleaned_data["specialty"],
                    notes=form.cleaned_data["notes"],
                    branch=form.cleaned_data["branch"],
                    consented_at=timezone.now(),
                )
        except AppointmentSlot.DoesNotExist:
            form.add_error(
                "slot", "That time is no longer available. Choose another slot."
            )
        except IntegrityError:
            form.add_error("slot", "That time was just booked. Choose another slot.")
        else:
            email_sent = _send_appointment_emails(booking)
            request.session["appointment_reference"] = str(booking.reference)
            request.session["appointment_email_warning"] = not email_sent
            return context, redirect(redirect_route)

    context.update(
        {
            "form": form,
            "has_available_slots": form.fields["slot"].queryset.exists(),
        }
    )
    return context, None


def services(request: HttpRequest) -> HttpResponse:
    booking_context, redirect_response = _process_appointment_booking(
        request, redirect_route="services"
    )
    if redirect_response is not None:
        return redirect_response

    category_rules = (
        ("General and outpatient care", ("general", "outpatient")),
        ("Diagnostics and pharmacy", ("laboratory", "diagnostic", "pharmacy")),
        ("Family and maternity care", ("maternity", "child", "family")),
        ("Emergency and referrals", ("emergency", "referral")),
    )
    service_categories = {title: [] for title, _ in category_rules}
    other_services = []
    for service in Service.objects.filter(is_active=True):
        service_name = service.name.casefold()
        category = next(
            (
                title
                for title, keywords in category_rules
                if any(keyword in service_name for keyword in keywords)
            ),
            None,
        )
        if category:
            service_categories[category].append(service)
        else:
            other_services.append(service)

    grouped_services = [
        {"title": title, "services": items}
        for title, items in service_categories.items()
        if items
    ]
    if other_services:
        grouped_services.append(
            {"title": "Other confirmed services", "services": other_services}
        )
    return _render_page(
        request,
        "services",
        {
            "service_groups": SERVICE_GROUPS,
            "service_categories": grouped_services,
            "service_reference": SERVICE_REFERENCE,
            "service_reference_note": SERVICE_REFERENCE_NOTE,
            **booking_context,
        },
    )


def contact(request: HttpRequest) -> HttpResponse:
    return _render_page(request, "contact")


def insurance(request: HttpRequest) -> HttpResponse:
    return _render_page(request, "insurance", {"insurers": INSURERS})


def privacy(request: HttpRequest) -> HttpResponse:
    if settings.APPOINTMENTS_ENABLED:
        appointment_privacy = (
            "When booking is enabled, the site collects your name, phone, email, "
            "chosen branch, specialty preference, service, appointment time, and "
            "optional appointment notes for practical logistics only. These "
            "details are used to manage your appointment "
            f"and are deleted after {settings.APPOINTMENT_RETENTION_DAYS} days. "
            "Do not submit symptoms, diagnoses, or medical history."
        )
    else:
        appointment_privacy = (
            "Online booking is not active, so this site is not collecting appointment details. "
            "Before booking is enabled, the clinic must approve its privacy notice and retention period."
        )
    return _render_page(
        request, "privacy", {"appointment_privacy": appointment_privacy}
    )


def _send_appointment_emails(appointment: Appointment) -> bool:
    local_start = timezone.localtime(appointment.slot.starts_at)
    service_name = appointment.slot.service.name
    time_label = local_start.strftime("%I:%M %p").lstrip("0")
    time_text = (
        f"{local_start:%A, %d %B %Y} at {time_label} (Uganda time)"
    )
    reference = str(appointment.reference)
    clinic_body = (
        "A new appointment has been confirmed.\n\n"
        f"Service: {service_name}\n"
        f"Specialty or care area: {appointment.specialty or 'Not specified'}\n"
        f"Branch: {appointment.get_branch_display() or 'Not specified'}\n"
        f"Time: {time_text}\n"
        f"Name: {appointment.full_name}\n"
        f"Phone: {appointment.phone}\n"
        f"Email: {appointment.email}\n"
        f"Reference: {reference}\n"
    )
    visitor_body = (
        "Your appointment with Karis Medical is confirmed.\n\n"
        f"Service: {service_name}\n"
        f"Specialty or care area: {appointment.specialty or 'Not specified'}\n"
        f"Branch: {appointment.get_branch_display() or 'Not specified'}\n"
        f"Time: {time_text}\n"
        f"Reference: {reference}\n\n"
        "Keep this reference for your records."
    )
    try:
        send_mail(
            "New Karis Medical appointment",
            clinic_body,
            settings.DEFAULT_FROM_EMAIL,
            [settings.APPOINTMENT_NOTIFICATION_EMAIL],
            fail_silently=False,
        )
        send_mail(
            "Karis Medical appointment confirmed",
            visitor_body,
            settings.DEFAULT_FROM_EMAIL,
            [appointment.email],
            fail_silently=False,
        )
    except Exception:
        logger.exception(
            "Appointment email delivery failed for reference %s", reference
        )
        return False
    return True


def appointments(request: HttpRequest) -> HttpResponse:
    booking_context, redirect_response = _process_appointment_booking(
        request, redirect_route="appointments"
    )
    if redirect_response is not None:
        return redirect_response

    context = {
        "facts": PUBLIC_FACTS,
        "page_title": "Appointments | Karis Medical",
        "branches": BRANCHES,
        "opening_hours": OPENING_HOURS,
        **booking_context,
    }
    return render(request, "clinic/appointments.html", context)


def staff_login(request: HttpRequest) -> HttpResponse:
    if _is_staff_user(request.user):
        return redirect("staff_dashboard")

    error_message = None
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            next_url = request.GET.get("next")
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            return redirect("staff_dashboard")
        error_message = "Invalid staff username or password."

    return render(
        request,
        "clinic/staff_login.html",
        {
            "page_title": "Staff Sign In | Karis Medical",
            "facts": PUBLIC_FACTS,
            "error_message": error_message,
        },
    )


@require_POST
def staff_logout(request: HttpRequest) -> HttpResponse:
    logout(request)
    return redirect("staff_login")


@user_passes_test(_is_staff_user, login_url="staff_login")
def staff_dashboard(request: HttpRequest) -> HttpResponse:
    now = timezone.now()
    status_filter = request.GET.get("status", "all")
    service_filter = request.GET.get("service", "")
    search_query = (request.GET.get("q") or "").strip()

    slot_form = StaffSlotForm()
    bulk_form = StaffBulkSlotForm()

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create_slot":
            slot_form = StaffSlotForm(request.POST)
            if slot_form.is_valid():
                try:
                    AppointmentSlot.objects.create(
                        service=slot_form.cleaned_data["service"],
                        starts_at=slot_form.cleaned_data["starts_at"],
                        ends_at=slot_form.cleaned_data["ends_at"],
                        is_active=True,
                    )
                except IntegrityError:
                    slot_form.add_error(
                        "start_time",
                        "A slot already exists for this service at that start time.",
                    )
                else:
                    messages.success(request, "Appointment slot created.")
                    return redirect("staff_dashboard")
        elif action == "bulk_generate":
            bulk_form = StaffBulkSlotForm(request.POST)
            if bulk_form.is_valid():
                created_count = 0
                tz = timezone.get_current_timezone()
                services_list = bulk_form.cleaned_data["services"]
                start_date = bulk_form.cleaned_data["start_date"]
                days = bulk_form.cleaned_data["days"]
                day_start = bulk_form.cleaned_data["day_start"]
                day_end = bulk_form.cleaned_data["day_end"]
                duration = timedelta(
                    minutes=int(bulk_form.cleaned_data["duration_minutes"])
                )

                for day_offset in range(days):
                    current_date = start_date + timedelta(days=day_offset)
                    end_boundary = timezone.make_aware(
                        datetime.combine(current_date, day_end), tz
                    )
                    for time_value in APPOINTMENT_TIMES:
                        slot_time = time.fromisoformat(time_value)
                        if not day_start <= slot_time <= day_end:
                            continue
                        cursor = timezone.make_aware(
                            datetime.combine(current_date, slot_time), tz
                        )
                        if cursor + duration > end_boundary:
                            continue
                        if cursor > now:
                            for svc in services_list:
                                _, created = AppointmentSlot.objects.get_or_create(
                                    service=svc,
                                    starts_at=cursor,
                                    defaults={
                                        "ends_at": cursor + duration,
                                        "is_active": True,
                                    },
                                )
                                if created:
                                    created_count += 1
                messages.success(
                    request,
                    f"Generated {created_count} new bookable appointment slots.",
                )
                return redirect("staff_dashboard")

    appointments_qs = Appointment.objects.select_related("slot__service").order_by(
        "slot__starts_at"
    )
    if status_filter in {Appointment.Status.CONFIRMED, Appointment.Status.CANCELLED}:
        appointments_qs = appointments_qs.filter(status=status_filter)
    if service_filter.isdigit():
        appointments_qs = appointments_qs.filter(slot__service_id=int(service_filter))
    if search_query:
        appointments_qs = appointments_qs.filter(
            Q(full_name__icontains=search_query)
            | Q(phone__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(reference__icontains=search_query)
        )

    upcoming_slots = (
        AppointmentSlot.objects.select_related("service")
        .annotate(
            confirmed_count=Count(
                "appointments",
                filter=Q(appointments__status=Appointment.Status.CONFIRMED),
            )
        )
        .filter(starts_at__gt=now)
        .order_by("starts_at")[:60]
    )

    total_confirmed = Appointment.objects.filter(
        status=Appointment.Status.CONFIRMED
    ).count()
    upcoming_confirmed = Appointment.objects.filter(
        status=Appointment.Status.CONFIRMED,
        slot__starts_at__gt=now,
    ).count()
    total_cancelled = Appointment.objects.filter(
        status=Appointment.Status.CANCELLED
    ).count()
    open_slots_count = (
        AppointmentSlot.objects.filter(
            is_active=True,
            starts_at__gt=now,
            service__is_active=True,
        )
        .exclude(appointments__status=Appointment.Status.CONFIRMED)
        .count()
    )

    return render(
        request,
        "clinic/staff_dashboard.html",
        {
            "page_title": "Staff Dashboard | Karis Medical",
            "facts": PUBLIC_FACTS,
            "appointments": appointments_qs[:100],
            "upcoming_slots": upcoming_slots,
            "services": Service.objects.order_by("name"),
            "slot_form": slot_form,
            "bulk_form": bulk_form,
            "status_filter": status_filter,
            "service_filter": service_filter,
            "search_query": search_query,
            "stats": {
                "total_confirmed": total_confirmed,
                "upcoming_confirmed": upcoming_confirmed,
                "total_cancelled": total_cancelled,
                "open_slots": open_slots_count,
            },
        },
    )


@user_passes_test(_is_staff_user, login_url="staff_login")
@require_POST
def staff_appointment_status(request: HttpRequest, pk: int) -> HttpResponse:
    appointment = get_object_or_404(Appointment.objects.select_related("slot"), pk=pk)
    new_status = request.POST.get("status")
    if new_status in {Appointment.Status.CONFIRMED, Appointment.Status.CANCELLED}:
        if (
            new_status == Appointment.Status.CONFIRMED
            and Appointment.objects.filter(
                slot=appointment.slot, status=Appointment.Status.CONFIRMED
            )
            .exclude(pk=appointment.pk)
            .exists()
        ):
            messages.error(
                request,
                "Cannot re-confirm because another confirmed booking already uses this slot.",
            )
        else:
            appointment.status = new_status
            appointment.save(update_fields=["status"])
            messages.success(
                request,
                f"Appointment for {appointment.full_name} marked as {appointment.get_status_display().lower()}.",
            )
    return redirect("staff_dashboard")


@user_passes_test(_is_staff_user, login_url="staff_login")
@require_POST
def staff_slot_toggle(request: HttpRequest, pk: int) -> HttpResponse:
    slot = get_object_or_404(AppointmentSlot, pk=pk)
    slot.is_active = not slot.is_active
    slot.save(update_fields=["is_active"])
    state_label = "enabled" if slot.is_active else "paused"
    messages.success(request, f"Slot {slot} {state_label}.")
    return redirect("staff_dashboard")


@user_passes_test(_is_staff_user, login_url="staff_login")
@require_POST
def staff_service_toggle(request: HttpRequest, pk: int) -> HttpResponse:
    service = get_object_or_404(Service, pk=pk)
    service.is_active = not service.is_active
    service.save(update_fields=["is_active"])
    state_label = "activated" if service.is_active else "deactivated"
    messages.success(request, f"Service '{service.name}' {state_label}.")
    return redirect("staff_dashboard")


def page_not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    return render(
        request,
        "clinic/404.html",
        {"page_title": "Page not found | Karis Medical", "facts": PUBLIC_FACTS},
        status=404,
    )
