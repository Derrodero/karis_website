from datetime import datetime, time, timedelta

import pytest
from django.core import mail
from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from clinic.models import Appointment, AppointmentSlot, Service

pytestmark = pytest.mark.django_db


def future_slot_start(days=2, slot_time="09:00"):
    naive_start = datetime.combine(
        timezone.localdate() + timedelta(days=days),
        time.fromisoformat(slot_time),
    )
    return timezone.make_aware(naive_start, timezone.get_current_timezone())


@pytest.mark.parametrize(
    "route_name",
    [
        "home",
        "about",
        "services",
        "contact",
        "insurance",
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


def test_appointments_is_a_header_button_not_a_main_navigation_item(client):
    response = client.get(reverse("home"))

    assert response.status_code == 200
    assert b'class="appointments-cta"' in response.content
    assert b'href="/appointments#service-booking"' in response.content
    assert b'data-page="appointments"' not in response.content
    nav = response.content.split(b'id="main-navigation"', 1)[1].split(b"</nav>", 1)[0]
    assert b"Appointments" not in nav


def test_insurance_page_lists_providers_and_adds_navigation_link(client):
    response = client.get(reverse("insurance"))

    assert response.status_code == 200
    assert b'data-current-page="insurance"' in response.content
    assert b'href="/insurance"' in response.content
    assert b"Listed insurance providers" in response.content
    for insurer, logo in (
        ("Britam", "britam.webp"),
        ("AAR", "aar.png"),
        ("APA", "apa.png"),
        ("Sanlam", "sanlam.png"),
        ("Prudential", "prudential.png"),
    ):
        assert insurer.encode() in response.content
        assert f"alt=\"{insurer} logo\"".encode() in response.content
        assert f"/static/clinic/images/karis%20medical%20images/{logo}".encode() in response.content
    assert b"Confirm that your policy is active" in response.content
    assert b"Contact your insurer to confirm your plan" in response.content
    assert b"pre-authorisation" in response.content


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
        "To glorify God through healthcare.",
        "To be the health care provider of choice for all Ugandans.",
        "Hospitality",
        "Excellence",
        "We strive for high-quality care through continuous learning, attention to detail, and improvement.",
        "Patient safety",
        "We listen with empathy and respond with kindness to every patient and family.",
        "We act honestly, protect confidentiality, and do what is right in every interaction.",
        "We welcome everyone warmly and help patients feel comfortable and cared for.",
        "We honour the dignity, choices, backgrounds, and individual needs of every person.",
        "We put safety first by being attentive, careful, and committed to reducing harm.",
        "bi-heart-pulse",
        "bi-shield-check",
        "bi-house-heart",
        "bi-trophy-fill",
        "bi-person-hearts",
        "bi-shield-plus",
        "Outpatient and consultation rooms",
        "Laboratory and diagnostic services",
        "Pharmacy",
        "Maternity and child health services",
        "Emergency and referral services",
        "Upcoming projects and future developments",
        "International Nursing School",
        "Along Gayaza Road, about 8 km from Kampala; branch off via Bobi Wine Road.",
        "Hospital construction in progress",
        "Proposed hospital design",
        "Nursing school construction in progress",
        "Multi-Story%20Building%20Under%20Construction.png",
        "Hospitalfinised%20view.jpg",
        "Nursingschoolsite.jpg",
        "Health education campaigns",
        "Community screening programmes",
        "Child health outreach",
        "Immunisation campaigns",
        "Partnerships with organisations",
        "Patient-growth figures and testimonial percentages are not published",
    ):
        assert fact.encode() in response.content
    value_order = [
        response.content.index(f">{value}</h4>".encode())
        for value in (
            "Compassion",
            "Hospitality",
            "Integrity",
            "Excellence",
            "Respect",
            "Patient safety",
        )
    ]
    assert value_order == sorted(value_order)
    assert b"Professionalism" not in response.content
    assert b"Teamwork" not in response.content
    for slug in (
        "medical-director",
        "doctors-specialists",
        "nurses-midwives",
        "laboratory-professionals",
        "pharmacists-health-workers",
    ):
        assert f'href="/about/{slug}"'.encode() in response.content
    assert b'href="/about/upcoming-projects"' in response.content

    assert response.content.index(
        b"Overview of Karis Medical"
    ) < response.content.index(b"Beyond care.")
    assert (
        response.content.index(b"Medical team and leadership")
        < response.content.index(b"Upcoming projects and future developments")
        < response.content.index(b"Community outreach and social responsibility")
    )
    assert (
        b"Further milestones will be added when the clinic supplies verified dates"
        in response.content
    )


@pytest.mark.parametrize(
    ("slug", "title", "detail", "section"),
    [
        (
            "medical-director",
            "Medical director or clinical administrator",
            "Leadership name, qualifications, and registration details pending clinic verification.",
            "Medical team and leadership",
        ),
        (
            "doctors-specialists",
            "Doctors and specialists",
            "Names, specialties, and verified credentials pending clinic approval.",
            "Medical team and leadership",
        ),
        (
            "nurses-midwives",
            "Nurses and midwives",
            "Team roster and professional credentials pending clinic verification.",
            "Medical team and leadership",
        ),
        (
            "laboratory-professionals",
            "Laboratory professionals",
            "Team roster and professional credentials pending clinic verification.",
            "Medical team and leadership",
        ),
        (
            "pharmacists-health-workers",
            "Pharmacists and other health workers",
            "Team roster and professional credentials pending clinic verification.",
            "Medical team and leadership",
        ),
        (
            "upcoming-projects",
            "Upcoming projects and future developments",
            "Karis Hospital and an international nursing school are under construction",
            "Looking ahead",
        ),
    ],
)
def test_about_subsection_links_open_dedicated_pages(client, slug, title, detail, section):
    response = client.get(reverse("about_detail", args=[slug]))

    assert response.status_code == 200
    assert title.encode() in response.content
    assert detail.encode() in response.content
    assert section.encode() in response.content
    if slug == "upcoming-projects":
        assert b"Information awaiting confirmation" not in response.content
        assert b"Under construction" in response.content
        assert b"Multi-Story%20Building%20Under%20Construction.png" in response.content
        assert b"Hospitalfinised%20view.jpg" in response.content
        assert b"Nursingschoolsite.jpg" in response.content
    else:
        assert b"Information awaiting confirmation" in response.content
    assert b'href="/about"' in response.content


def test_unknown_about_subsection_returns_not_found(client):
    response = client.get(reverse("about_detail", args=["unknown-subsection"]))

    assert response.status_code == 404


def test_founder_and_executive_team_page_uses_verified_profile_placeholders(client):
    about_response = client.get(reverse("about"))
    assert b'href="/about/medical-team"' in about_response.content
    assert b'href="/find-a-doctor"' in about_response.content

    response = client.get(reverse("about_detail", args=["medical-team"]))

    assert response.status_code == 200
    assert b"AGABA ANDY CHRISTIAN" in response.content
    assert b"Founder of Karis Medical." in response.content
    assert response.content.count(b'class="team-member-card"') == 5
    assert response.content.count(b"View profile") == 5
    team_section = response.content.split(
        b'aria-label="Founder and executive team"', 1
    )[1].split(b"</section>", 1)[0]
    assert team_section.count(b"Request appointment") == 5
    assert b"Photo pending confirmation" in response.content


def test_find_doctor_page_renders_twenty_filterable_profile_cards(client):
    response = client.get(reverse("find_doctor"))

    assert response.status_code == 200
    assert response.content.count(b'data-doctor-card') == 20
    assert response.content.count(b'data-specialty-filter') == 20
    assert b'data-doctor-search' in response.content
    assert b'data-doctor-branch' in response.content
    assert b"Women" in response.content
    assert b"gynaecology" in response.content
    assert b"Orthopaedics" in response.content
    assert b"Emergency care" in response.content
    assert b"Pharmacy" in response.content
    assert b"Profiles below are placeholders" in response.content
    assert b"doctor-directory.js" in response.content


def test_team_and_doctor_profile_links_resolve(client):
    team_response = client.get(reverse("about_detail", args=["founder"]))
    doctor_response = client.get(
        reverse("doctor_profile", args=["specialist-profile-01"])
    )

    assert team_response.status_code == 200
    assert b"AGABA ANDY CHRISTIAN" in team_response.content
    assert doctor_response.status_code == 200
    assert b"General practice" in doctor_response.content
    assert b"PROFILE PENDING CONFIRMATION" in doctor_response.content


def test_unknown_doctor_profile_returns_not_found(client):
    response = client.get(reverse("doctor_profile", args=["unknown-profile"]))

    assert response.status_code == 404


def test_contact_page_has_no_submission_form(client):
    response = client.get(reverse("contact"))

    assert response.status_code == 200
    assert b"<form" not in response.content
    assert b'class="contact-directory"' in response.content
    assert response.content.count(b'class="branch-card"') == 2
    assert b'href="tel:0393001567"' in response.content
    assert b'href="tel:0393104667"' in response.content
    assert b'href="mailto:help@karisclinic.com"' in response.content
    assert b"help@karisclinic.com" in response.content
    assert b'href="https://www.google.com/maps/place/Karis+Medical+Kyanja/' in response.content
    assert b'href="https://www.google.com/maps/place/Karis+Medical+Naalya/' in response.content
    assert response.content.count(b"View location on map") == 2


def test_accepted_insurance_logos_are_available_in_the_site_footer(client):
    response = client.get(reverse("home"))

    assert response.status_code == 200
    assert b'data-insurance-track' in response.content
    assert b'data-insurance-toggle' in response.content
    assert b'href="/insurance"' in response.content
    for insurer in ("Britam", "AAR", "APA", "Sanlam", "Prudential"):
        assert insurer.encode() in response.content


def test_home_branch_cards_link_to_their_google_maps_locations(client):
    response = client.get(reverse("home"))

    assert response.status_code == 200
    assert b'href="https://www.google.com/maps/place/Karis+Medical+Kyanja/' in response.content
    assert b'href="https://www.google.com/maps/place/Karis+Medical+Naalya/' in response.content
    assert b'aria-label="View Kyanja branch location on Google Maps"' in response.content
    assert b'aria-label="View Naalya branch location on Google Maps"' in response.content


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
    start = future_slot_start()
    slot = AppointmentSlot.objects.create(
        service=service,
        starts_at=start,
        ends_at=start + timedelta(minutes=30),
    )

    response = client.get(reverse("appointments"))

    assert response.status_code == 200
    assert b'class="booking-form booking-wizard"' in response.content
    assert b"Appointment steps" in response.content
    assert b"Where would you like to be seen?" in response.content
    assert b"Clinic-approved visit" in response.content
    assert f'data-service="{service.pk}"'.encode() in response.content
    assert f'value="{slot.pk}"'.encode() in response.content
    assert (
        f'data-date="{timezone.localtime(slot.starts_at).date().isoformat()}"'.encode()
        in response.content
    )
    assert b'data-time="09:00"' in response.content
    assert b'type="date"' in response.content


@override_settings(APPOINTMENTS_ENABLED=True, APPOINTMENT_RETENTION_DAYS=90)
def test_doctor_specialty_prefills_the_appointment_preference(client):
    service = Service.objects.create(name="Clinic-approved visit", is_active=True)
    start = future_slot_start()
    AppointmentSlot.objects.create(
        service=service,
        starts_at=start,
        ends_at=start + timedelta(minutes=30),
    )

    response = client.get(reverse("appointments"), {"specialty": "Paediatrics"})

    assert response.status_code == 200
    assert (
        b'<option value="Paediatrics" selected>Paediatrics</option>'
        in response.content
    )


@override_settings(APPOINTMENTS_ENABLED=True, APPOINTMENT_RETENTION_DAYS=90)
def test_booking_offers_all_published_custom_times(client):
    service = Service.objects.create(name="Clinic-approved visit", is_active=True)
    for slot_time in ("09:00", "10:30", "12:00", "14:00", "15:30", "11:00", "11:17"):
        start = future_slot_start(days=3, slot_time=slot_time)
        AppointmentSlot.objects.create(
            service=service,
            starts_at=start,
            ends_at=start + timedelta(minutes=30),
        )

    response = client.get(reverse("appointments"))

    assert response.status_code == 200
    for slot_time in ("09:00", "10:30", "12:00", "14:00", "15:30", "11:00", "11:17"):
        assert f'data-time="{slot_time}"'.encode() in response.content


@override_settings(
    APPOINTMENTS_ENABLED=True,
    APPOINTMENT_NOTIFICATION_EMAIL="appointments@example.test",
    APPOINTMENT_RETENTION_DAYS=90,
    DEFAULT_FROM_EMAIL="noreply@example.test",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
def test_booking_rejects_a_date_that_does_not_match_the_selected_slot(client):
    service = Service.objects.create(name="Clinic-approved visit", is_active=True)
    start = future_slot_start()
    slot = AppointmentSlot.objects.create(
        service=service,
        starts_at=start,
        ends_at=start + timedelta(minutes=30),
    )

    response = client.post(
        reverse("appointments"),
        {
            "branch": "kyanja",
            "full_name": "Amina N.",
            "phone": "+256 700 000 000",
            "email": "amina@example.test",
            "service": service.pk,
            "date": (
                timezone.localtime(slot.starts_at).date() + timedelta(days=1)
            ).isoformat(),
            "slot": slot.pk,
            "consent": "on",
        },
    )

    assert response.status_code == 200
    assert b"Choose an available time on the selected date." in response.content
    assert not Appointment.objects.filter(slot=slot).exists()


@override_settings(APPOINTMENTS_ENABLED=True, APPOINTMENT_RETENTION_DAYS=90)
def test_privacy_page_discloses_booking_fields_and_retention(client):
    response = client.get(reverse("privacy"))

    assert b"collects your name, phone, email" in response.content
    assert b"deleted after 90 days" in response.content
    assert b"Do not submit symptoms, diagnoses, or medical history" in response.content
    assert b"optional appointment notes" in response.content
    assert b"practical logistics only" in response.content
    assert b"appointment notes" in response.content


@override_settings(
    APPOINTMENTS_ENABLED=True,
    APPOINTMENT_NOTIFICATION_EMAIL="appointments@example.test",
    APPOINTMENT_RETENTION_DAYS=90,
    DEFAULT_FROM_EMAIL="noreply@example.test",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
def test_appointment_page_renders_the_five_step_booking_flow(client):
    service = Service.objects.create(name="Clinic-approved visit", is_active=True)
    start = future_slot_start()
    AppointmentSlot.objects.create(
        service=service,
        starts_at=start,
        ends_at=start + timedelta(minutes=30),
    )

    response = client.get(reverse("appointments"))

    assert response.status_code == 200
    for step in (
        "Location",
        "Service",
        "Date",
        "Time",
        "Summary &amp; Details",
        "Kyanja branch",
        "Naalya branch",
        "Choose a date",
        "Choose an available time",
        "Appointment summary",
    ):
        assert step.encode() in response.content
    assert response.content.count(b'data-wizard-panel="') == 5


def test_no_availability_explains_schedule_and_offers_branch_calls(client):
    response = client.get(reverse("appointments"))

    assert response.status_code == 200
    assert b"Online appointment requests are not available yet." in response.content
    assert b"the clinic has not published any future" in response.content
    assert b"appointment times. Please contact a branch" in response.content
    assert b'href="tel:0393001567"' in response.content
    assert b'href="tel:0393104667"' in response.content


@override_settings(
    APPOINTMENTS_ENABLED=True,
    APPOINTMENT_NOTIFICATION_EMAIL="appointments@example.test",
    APPOINTMENT_RETENTION_DAYS=90,
    DEFAULT_FROM_EMAIL="noreply@example.test",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
def test_booking_confirms_and_emails_both_parties(client):
    service = Service.objects.create(name="Clinic-approved visit", is_active=True)
    start = future_slot_start()
    slot = AppointmentSlot.objects.create(
        service=service,
        starts_at=start,
        ends_at=start + timedelta(minutes=30),
    )

    response = client.post(
        reverse("appointments"),
        {
            "branch": "kyanja",
            "full_name": "Amina N.",
            "phone": "+256 700 000 000",
            "email": "amina@example.test",
            "service": service.pk,
            "specialty": "Paediatrics",
            "date": timezone.localtime(slot.starts_at).date().isoformat(),
            "slot": slot.pk,
            "notes": "Please call upon arrival.",
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
    appointment = Appointment.objects.get(slot=slot)
    assert appointment.branch == "kyanja"
    assert appointment.specialty == "Paediatrics"
    assert appointment.notes == "Please call upon arrival."
    assert "Please call upon arrival." not in mail.outbox[0].body
    assert "Specialty or care area: Paediatrics" in mail.outbox[0].body
    assert "Branch: Kyanja branch" in mail.outbox[0].body
    assert "Branch: Kyanja branch" in mail.outbox[1].body


@override_settings(
    APPOINTMENTS_ENABLED=True,
    APPOINTMENT_NOTIFICATION_EMAIL="appointments@example.test",
    APPOINTMENT_RETENTION_DAYS=90,
    DEFAULT_FROM_EMAIL="noreply@example.test",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
def test_booked_slot_cannot_be_reserved_twice(client):
    service = Service.objects.create(name="Clinic-approved visit", is_active=True)
    start = future_slot_start()
    slot = AppointmentSlot.objects.create(
        service=service,
        starts_at=start,
        ends_at=start + timedelta(minutes=30),
    )
    booking_data = {
        "branch": "naalya",
        "full_name": "Amina N.",
        "phone": "+256 700 000 000",
        "email": "amina@example.test",
        "service": service.pk,
        "date": timezone.localtime(slot.starts_at).date().isoformat(),
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
        assert b'href="https://wa.me/256791234493"' in response.content
        assert b'href="https://wa.me/256393104667"' not in response.content
        assert b'aria-label="WhatsApp Kyanja branch"' in response.content
        assert b'aria-label="WhatsApp Naalya branch"' not in response.content
        for destination in (
            b'href="https://www.instagram.com/karismedical/"',
            b'href="https://x.com/karismedical"',
            b'href="https://www.tiktok.com/@karismedical"',
        ):
            assert destination in response.content
        assert b"bi-facebook" not in response.content


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


def test_services_page_groups_the_requested_care_areas(client):
    response = client.get(reverse("services"))

    assert response.status_code == 200
    assert b'id="service-groups"' in response.content
    assert response.content.count(b'class="service-group-image"') == 5
    assert response.content.count(b'class="service-group-item"') == 14
    assert b"clinic/images/karis%20medical%20images/laboratory.webp" in response.content
    assert b"clinic/images/karis%20medical%20images/ambulance.webp" in response.content
    groups_section = response.content.split(b'id="service-groups"', 1)[1].split(
        b"</div>", 1
    )[0]
    assert b"<ul>" not in groups_section
    group_titles = (
        "Specialties",
        "Tests and Diagnostics",
        "Health check packages",
        "Maternity and Child Health",
        "Emergency and Urgent Care",
    )
    group_positions = [response.content.index(title.encode()) for title in group_titles]
    assert group_positions == sorted(group_positions)
    for service_detail in (
        "Paediatric care for children.",
        "Care for bones, joints, and mobility.",
        "Maternity and gynaecology care.",
        "Blood tests and other clinical testing.",
        "Diagnostic procedures.",
        "Comprehensive health screening.",
        "Preventive health screening for men.",
        "Preventive health screening for women.",
        "Paediatric wellness care.",
        "Pregnancy and delivery care.",
        "Care focused on reproductive health.",
        "Emergency care available 24 hours a day.",
        "Emergency transport.",
        "Services available to book online",
    ):
        assert service_detail.encode() in response.content


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
    start = future_slot_start()
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
    assert b'type="time"' in dashboard_resp.content
    assert b'name="start_time"' in dashboard_resp.content
    for preset in ("09:30", "10:30", "11:30", "14:30", "15:00"):
        assert f'data-start-time="{preset}"'.encode() in dashboard_resp.content

    service = Service.objects.filter(is_active=True).first()
    future_date = (timezone.localdate() + timedelta(days=3)).isoformat()
    create_slot_resp = client.post(
        reverse("staff_dashboard"),
        {
            "action": "create_slot",
            "service": service.pk,
            "date": future_date,
            "start_time": "10:17",
            "duration_minutes": "60",
        },
        follow=True,
    )
    assert create_slot_resp.status_code == 200
    slot = AppointmentSlot.objects.get(
        service=service,
        starts_at=future_slot_start(days=3, slot_time="10:17"),
    )

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


def test_staff_bulk_schedule_uses_custom_start_and_end_times(
    client, django_user_model
):
    staff = django_user_model.objects.create_user(
        username="schedule-manager",
        password="password",
        is_staff=True,
    )
    client.force_login(staff)
    service = Service.objects.create(name="Custom schedule service", is_active=True)
    start_date = timezone.localdate() + timedelta(days=3)

    response = client.post(
        reverse("staff_dashboard"),
        {
            "action": "bulk_generate",
            "services": [service.pk],
            "start_date": start_date.isoformat(),
            "days": "1",
            "day_start": "09:15",
            "day_end": "11:15",
            "duration_minutes": "60",
        },
        follow=True,
    )

    assert response.status_code == 200
    slots = list(
        AppointmentSlot.objects.filter(service=service)
        .order_by("starts_at")
        .values_list("starts_at", "ends_at")
    )
    assert len(slots) == 2
    assert timezone.localtime(slots[0][0]).strftime("%H:%M") == "09:15"
    assert timezone.localtime(slots[1][0]).strftime("%H:%M") == "10:15"


@override_settings(
    APPOINTMENTS_ENABLED=True,
    APPOINTMENT_NOTIFICATION_EMAIL="help@karisclinic.com",
    APPOINTMENT_RETENTION_DAYS=90,
    DEFAULT_FROM_EMAIL="help@karisclinic.com",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
def test_services_page_renders_and_submits_appointment_booking_form(client):
    service = Service.objects.filter(is_active=True).first()
    start = future_slot_start()
    slot = AppointmentSlot.objects.create(
        service=service,
        starts_at=start,
        ends_at=start + timedelta(minutes=30),
    )

    get_resp = client.get(reverse("services"))
    assert get_resp.status_code == 200
    assert b'class="booking-form booking-wizard"' in get_resp.content
    assert f'data-select-service="{service.pk}"'.encode() in get_resp.content
    assert b"Staff Login" in get_resp.content

    post_resp = client.post(
        reverse("services"),
        {
            "branch": "naalya",
            "full_name": "Sarah K.",
            "phone": "039 300 1567",
            "email": "sarah@example.test",
            "service": service.pk,
            "date": timezone.localtime(slot.starts_at).date().isoformat(),
            "slot": slot.pk,
            "consent": "on",
        },
        follow=True,
    )
    assert post_resp.status_code == 200
    assert b"Appointment confirmed" in post_resp.content
    assert Appointment.objects.filter(
        slot=slot, status=Appointment.Status.CONFIRMED, branch="naalya"
    ).exists()
