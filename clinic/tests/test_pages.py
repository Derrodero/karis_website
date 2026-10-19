from datetime import timedelta

import pytest
from django.core import mail
from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from clinic.models import Appointment, AppointmentSlot, Service

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "route_name",
    [
        "home",
        "about",
        "services",
        "contact",
        "appointments",
        "privacy",
    ],
)
def test_public_pages_render_successfully(client, route_name):
    response = client.get(reverse(route_name))

    assert response.status_code == 200
    assert b"Karis" in response.content
    assert b"Uganda" in response.content
    assert f'data-current-page="{route_name}"'.encode() in response.content
    assert b"logo_karis_meducal.PNG" in response.content
    assert b"Beyond Care" in response.content
    assert b'content="#3288f7"' in response.content


@pytest.mark.parametrize(
    ("route_name", "expected_text"),
    [
        ("about", "Staff names, qualifications, and credentials"),
        ("services", "General practice"),
        ("contact", "does not accept appointment requests"),
        ("privacy", "Appointment details are used only to manage your visit"),
    ],
)
def test_unverified_staff_details_remain_unpublished(client, route_name, expected_text):
    response = client.get(reverse(route_name))

    assert response.status_code == 200
    assert expected_text.encode() in response.content


def test_about_page_publishes_confirmed_profile_and_marks_unverified_claims(client):
    response = client.get(reverse("about"))

    for fact in (
        "Overview of Karis Medical",
        "Beyond care.",
        "Compassionate care and a healthier community.",
        "April 2025",
        "To develop the healthcare industry.",
        "To create a healthy community and make quality health services accessible.",
        "Hospitality",
        "Patient safety",
        "Outpatient and consultation rooms",
        "Laboratory and diagnostic services",
        "Pharmacy",
        "Maternity and child health services",
        "Emergency and referral services",
        "Health education campaigns",
        "Community screening programmes",
        "Child health outreach",
        "Immunisation campaigns",
        "Partnerships with organisations",
        "Patient-growth figures and testimonial percentages are not published",
    ):
        assert fact.encode() in response.content
    assert (
        b"Names, specialties, and verified credentials pending clinic approval"
        in response.content
    )

    assert response.content.index(
        b"Overview of Karis Medical"
    ) < response.content.index(b"Beyond care.")
    assert (
        b"Further milestones will be added when the clinic supplies verified dates"
        in response.content
    )


def test_contact_page_has_no_submission_form(client):
    response = client.get(reverse("contact"))

    assert response.status_code == 200
    assert b"<form" not in response.content
    assert b'class="contact-directory"' in response.content
    assert response.content.count(b'class="branch-card"') == 2
    assert b'href="tel:0393001567"' in response.content
    assert b'href="tel:0393104667"' in response.content
    assert b'href="mailto:care@karismedical.org"' in response.content
    assert b"care@karismedical.org" in response.content


@override_settings(APPOINTMENTS_ENABLED=False)
def test_appointment_page_does_not_collect_data_until_configured(client):
    response = client.get(reverse("appointments"))

    assert response.status_code == 200
    assert b"Online booking is not active yet" in response.content
    assert b"<form" not in response.content


@override_settings(APPOINTMENTS_ENABLED=False)
def test_home_does_not_claim_booking_is_active_before_configuration(client):
    response = client.get(reverse("home"))

    assert b"Appointment information" in response.content
    assert b"Book an appointment" not in response.content


def test_home_hero_uses_welcome_copy_and_requested_slideshow_images(client):
    response = client.get(reverse("home"))

    assert b"Welcome to Karis Medical." in response.content
    assert b"Kyanja branch or Naalya branch" in response.content
    assert b"Clear information." not in response.content
    assert b"5ce80a1d-b099-41ce-adb3-3cd18e7cf968.png" in response.content
    assert b"smiling-black-doctor-patient_605022-76344.jpg" in response.content
    assert b"home-slider.js" in response.content
    assert b"data-slide-previous" not in response.content
    assert b"data-slide-toggle" not in response.content
    assert b"data-slide-next" not in response.content


@override_settings(APPOINTMENTS_ENABLED=True, APPOINTMENT_RETENTION_DAYS=90)
def test_configured_appointment_page_renders_available_slot(client):
    service = Service.objects.create(name="Clinic-approved visit", is_active=True)
    start = timezone.now() + timedelta(days=2)
    slot = AppointmentSlot.objects.create(
        service=service,
        starts_at=start,
        ends_at=start + timedelta(minutes=30),
    )

    response = client.get(reverse("appointments"))

    assert response.status_code == 200
    assert b'form class="booking-form"' in response.content
    assert b"Clinic-approved visit" in response.content
    assert f'data-service="{service.pk}"'.encode() in response.content
    assert f'value="{slot.pk}"'.encode() in response.content


@override_settings(APPOINTMENTS_ENABLED=True, APPOINTMENT_RETENTION_DAYS=90)
def test_privacy_page_discloses_booking_fields_and_retention(client):
    response = client.get(reverse("privacy"))

    assert b"collects your name, phone, email" in response.content
    assert b"deleted after 90 days" in response.content
    assert b"No symptoms or medical history are requested" in response.content


@override_settings(
    APPOINTMENTS_ENABLED=True,
    APPOINTMENT_NOTIFICATION_EMAIL="appointments@example.test",
    APPOINTMENT_RETENTION_DAYS=90,
    DEFAULT_FROM_EMAIL="noreply@example.test",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
def test_booking_confirms_and_emails_both_parties(client):
    service = Service.objects.create(name="Clinic-approved visit", is_active=True)
    start = timezone.now() + timedelta(days=2)
    slot = AppointmentSlot.objects.create(
        service=service,
        starts_at=start,
        ends_at=start + timedelta(minutes=30),
    )

    response = client.post(
        reverse("appointments"),
        {
            "full_name": "Amina N.",
            "phone": "+256 700 000 000",
            "email": "amina@example.test",
            "service": service.pk,
            "slot": slot.pk,
            "consent": "on",
        },
        follow=True,
    )

    assert response.status_code == 200
    assert b"Appointment confirmed" in response.content
    assert (
        Appointment.objects.filter(
            slot=slot, status=Appointment.Status.CONFIRMED
        ).count()
        == 1
    )
    assert len(mail.outbox) == 2
    assert mail.outbox[0].to == ["appointments@example.test"]
    assert mail.outbox[1].to == ["amina@example.test"]


@override_settings(
    APPOINTMENTS_ENABLED=True,
    APPOINTMENT_NOTIFICATION_EMAIL="appointments@example.test",
    APPOINTMENT_RETENTION_DAYS=90,
    DEFAULT_FROM_EMAIL="noreply@example.test",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
def test_booked_slot_cannot_be_reserved_twice(client):
    service = Service.objects.create(name="Clinic-approved visit", is_active=True)
    start = timezone.now() + timedelta(days=2)
    slot = AppointmentSlot.objects.create(
        service=service,
        starts_at=start,
        ends_at=start + timedelta(minutes=30),
    )
    booking_data = {
        "full_name": "Amina N.",
        "phone": "+256 700 000 000",
        "email": "amina@example.test",
        "service": service.pk,
        "slot": slot.pk,
        "consent": "on",
    }
    client.post(reverse("appointments"), booking_data)

    response = client.post(reverse("appointments"), booking_data)

    assert response.status_code == 200
    assert (
        Appointment.objects.filter(
            slot=slot, status=Appointment.Status.CONFIRMED
        ).count()
        == 1
    )


def test_services_page_shows_only_active_services(client):
    Service.objects.create(name="Approved service", is_active=True)
    Service.objects.create(name="Unpublished draft", is_active=False)

    response = client.get(reverse("services"))

    assert b"Approved service" in response.content
    assert b"Unpublished draft" not in response.content


def test_home_and_contact_publish_branches_and_icon_links(client):
    for route_name in ("home", "contact"):
        response = client.get(reverse(route_name))
        for detail in (
            "Westmall, Kisasi Road, Kyanja, Kampala, Uganda",
            "039 300 1567",
            "Ground Floor, Naalya Heights, Naalya-Namugongo Road, Kampala, Uganda",
            "039 310 4667",
            "Open 24 hours, Monday to Sunday",
        ):
            assert detail.encode() in response.content
        assert b'href="https://wa.me/256393001567"' in response.content
        assert b'href="https://wa.me/256393104667"' not in response.content
        assert b'aria-label="WhatsApp Kyanja branch"' in response.content
        assert b'aria-label="WhatsApp Naalya branch"' not in response.content
        for destination in (
            b'href="https://www.instagram.com/"',
            b'href="https://www.facebook.com/"',
            b'href="https://x.com/"',
            b'href="https://www.tiktok.com/"',
        ):
            assert destination in response.content


def test_services_page_lists_the_three_clinic_services(client):
    response = client.get(reverse("services"))

    assert b"Service directory" in response.content
    assert b'class="service-accordion"' in response.content
    assert b"Diagnostics and pharmacy" in response.content
    assert b"Family and maternity care" in response.content
    assert b"{% elif" not in response.content
    for service_name in (
        "General practice",
        "Outpatient care",
        "Laboratory",
        "Pharmacy",
        "Maternity and child health services",
        "Emergency and referral services",
    ):
        assert service_name.encode() in response.content


def test_case_med_service_reference_is_separate_from_confirmed_karis_services(client):
    response = client.get(reverse("services"))

    for detail in (
        "Services to confirm with Karis",
        "published by CaseMed Services",
        "not confirmation that Karis Medical offers each service",
        "Radiology, including X-ray and ultrasound",
        "HIV counselling, testing, and treatment",
        "Cardiothoracic surgery",
        "Speech and language therapy",
        "24-hour ambulance service",
    ):
        assert detail.encode() in response.content
    assert response.content.index(b"Service directory") < response.content.index(
        b"Services to confirm with Karis"
    )
    assert not Service.objects.filter(name="Dental care", is_active=True).exists()


def test_legacy_patient_information_url_redirects_to_contact(client):
    response = client.get(reverse("patient_information"))

    assert response.status_code == 301
    assert response["Location"] == reverse("contact")


def test_staff_admin_requires_authentication(client):
    response = client.get("/staff/")

    assert response.status_code == 302
    assert response.url.startswith("/staff/login/")


@override_settings(APPOINTMENT_RETENTION_DAYS=30)
def test_retention_command_deletes_expired_booking_contact_details():
    service = Service.objects.create(name="Clinic-approved visit", is_active=True)
    start = timezone.now() + timedelta(days=2)
    slot = AppointmentSlot.objects.create(
        service=service,
        starts_at=start,
        ends_at=start + timedelta(minutes=30),
    )
    appointment = Appointment.objects.create(
        slot=slot,
        full_name="Amina N.",
        phone="+256 700 000 000",
        email="amina@example.test",
        consented_at=timezone.now(),
    )
    Appointment.objects.filter(pk=appointment.pk).update(
        created_at=timezone.now() - timedelta(days=31)
    )

    call_command("purge_expired_appointments")

    assert not Appointment.objects.filter(pk=appointment.pk).exists()


def test_unknown_page_returns_custom_not_found(client):
    response = client.get("/not-a-page")

    assert response.status_code == 404
    assert b"This page is unavailable" in response.content


def test_staff_dashboard_requires_login_and_allows_slot_and_booking_management(
    client, django_user_model
):
    unauth = client.get(reverse("staff_dashboard"))
    assert unauth.status_code == 302
    assert reverse("staff_login") in unauth.url

    django_user_model.objects.create_user(
        username="admin",
        password="password",
        is_staff=True,
        is_superuser=True,
    )
    login_resp = client.post(
        reverse("staff_login"),
        {"username": "admin", "password": "password"},
    )
    assert login_resp.status_code == 302
    assert login_resp.url == reverse("staff_dashboard")

    home_resp = client.get(reverse("home"))
    assert b"Sign out" in home_resp.content
    assert b"utility-logout-form" in home_resp.content

    dashboard_resp = client.get(reverse("staff_dashboard"))
    assert dashboard_resp.status_code == 200
    assert b"Appointment &amp; Schedule Dashboard" in dashboard_resp.content

    service = Service.objects.filter(is_active=True).first()
    future_date = (timezone.localdate() + timedelta(days=3)).isoformat()
    create_slot_resp = client.post(
        reverse("staff_dashboard"),
        {
            "action": "create_slot",
            "service": service.pk,
            "date": future_date,
            "start_time": "10:00",
            "duration_minutes": "60",
        },
        follow=True,
    )
    assert create_slot_resp.status_code == 200
    slot = AppointmentSlot.objects.filter(service=service).first()
    assert slot is not None

    appt = Appointment.objects.create(
        slot=slot,
        full_name="John Mukasa",
        phone="039 300 1567",
        email="john@example.test",
        consented_at=timezone.now(),
    )
    cancel_resp = client.post(
        reverse("staff_appointment_status", args=[appt.pk]),
        {"status": Appointment.Status.CANCELLED},
    )
    assert cancel_resp.status_code == 302
    appt.refresh_from_db()
    assert appt.status == Appointment.Status.CANCELLED

    logout_resp = client.post(reverse("staff_logout"))
    assert logout_resp.status_code == 302
    assert client.get(reverse("staff_dashboard")).url.startswith(reverse("staff_login"))


@override_settings(
    APPOINTMENTS_ENABLED=True,
    APPOINTMENT_NOTIFICATION_EMAIL="care@karismedical.org",
    APPOINTMENT_RETENTION_DAYS=90,
    DEFAULT_FROM_EMAIL="care@karismedical.org",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
def test_services_page_renders_and_submits_appointment_booking_form(client):
    service = Service.objects.filter(is_active=True).first()
    start = timezone.now() + timedelta(days=2)
    slot = AppointmentSlot.objects.create(
        service=service,
        starts_at=start,
        ends_at=start + timedelta(minutes=30),
    )

    get_resp = client.get(reverse("services"))
    assert get_resp.status_code == 200
    assert b'form class="booking-form"' in get_resp.content
    assert f'data-select-service="{service.pk}"'.encode() in get_resp.content
    assert b"Staff Login" in get_resp.content

    post_resp = client.post(
        reverse("services"),
        {
            "full_name": "Sarah K.",
            "phone": "039 300 1567",
            "email": "sarah@example.test",
            "service": service.pk,
            "slot": slot.pk,
            "consent": "on",
        },
        follow=True,
    )
    assert post_resp.status_code == 200
    assert b"Appointment confirmed" in post_resp.content
    assert Appointment.objects.filter(
        slot=slot, status=Appointment.Status.CONFIRMED
    ).exists()
