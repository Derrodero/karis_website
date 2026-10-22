# Karis Medical

A server-rendered Django website for verified public clinic information and clinic-managed appointment slots. It does not collect symptoms or medical history.

## Local development

Requires Python 3.12 and pip.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. Staff manage approved services and future appointment slots at `/staff/`. Run tests with `python -m pytest`.

## Appointment setup

Online booking is disabled until the clinic configures host SMTP, an approved privacy notice, and a positive appointment-retention period. For local development, copy `.env.example` to `.env` and add the SMTP credentials; booking notifications default to `help@karisclinic.com`. The `.env` file is git-ignored and must never be committed. Set `APPOINTMENT_PRIVACY_APPROVED=true` only after the clinic has reviewed the displayed data notice. The confirmed services are added by migration. Sign in at `/staff/`, verify the services, and add future slots. Each slot accepts one active appointment; no appointment times are seeded.

The appointment request follows five steps: choose a branch, an approved service, an optional care-area preference, a date, and an available time, then review the summary and submit contact details. The calendar only offers staff-published slots at 9:00 AM, 10:30 AM, 12:00 PM, 2:00 PM, or 3:30 PM. Appointment records contain name, phone, email, branch, specialty preference, service/time, optional practical appointment notes, consent time, status, and a reference. Notes are for logistics only; do not submit symptoms or medical history. Notes are visible to authorized staff in the dashboard/admin and are excluded from email notifications. Current availability is managed by service and shared across the two branch choices; staff should confirm branch-specific availability when needed. Staff must run `python manage.py purge_expired_appointments` regularly; the command uses the configured retention period. A staff superuser is required to manage schedules and view bookings.

Docker Compose is also provided for local development: `docker compose up --build`.

## Public content

Confirmed public facts are Karis Medical in Uganda, established in April 2025, with two Kampala branches (Kyanja: Westmall, Kisasi Road, Kyanja, Kampala, Uganda; 039 300 1567. Naalya: Ground Floor, Naalya Heights, Naalya-Namugongo Road, Kampala, Uganda; 039 310 4667), 24-hour opening every day, and general practice, outpatient care, laboratory, pharmacy, maternity/child health, and emergency/referral services. The About page includes the supplied slogan, mission, vision, values, facilities, and outreach priorities. It also presents Karis Hospital and an international nursing school as projects under construction along Gayaza Road, about 8 km from Kampala via Bobi Wine Road; the hospital rendering is labeled as a proposed design. The Insurance page lists Britam, AAR, APA, Sanlam, and Prudential as providers reported by the clinic, and advises patients to confirm policy-specific cover and requirements before visiting. Team names/credentials and quantified patient-growth/testimonial claims remain unpublished pending verification. The icon-only WhatsApp link opens a chat at `https://wa.me/256791234493`; the Instagram, X, and TikTok icons link to the clinic profiles at `https://www.instagram.com/karismedical/`, `https://x.com/karismedical`, and `https://www.tiktok.com/@karismedical`. Contact email is `help@karisclinic.com`. The supplied Karis logo and "Beyond Care" tagline appear in the shared header. The Services page keeps those Karis-approved services separate from the CaseMed Services reference catalogue, which is explicitly not a claim of Karis availability. Branch addresses and hours are available from Contact, with clickable Google Maps location links for each branch; the legacy `/patient-information` URL permanently redirects there.

About-page medical-team roles and the upcoming-projects subsection link to dedicated detail pages. Unverified staff and project information is explicitly marked as pending confirmation.

## Visual design

The original Karis design uses sky-blue surfaces, serif display headings, patient shortcuts, a full-width Home slideshow, and contextual photography across About, Services, Patient Information, Contact, and Appointments. Supplied photos are not labeled as named staff or specific branch premises without verification. The mobile navigation supports keyboard dismissal; navigation remains visible if JavaScript is unavailable. Light, dark, and system themes are supported, and the slideshow pauses for reduced-motion preferences. Increment the asset version in the base template when publishing updated styles or theme/navigation scripts.

## cPanel deployment

The workspace plan does not confirm the cPanel account's Python, Django, WSGI/Passenger, or database support. Verify those capabilities with the host before deployment. If supported, configure a Python 3.12 application with the project root, `passenger_wsgi.py`, and WSGI callable `application`; install `requirements.txt` in the host-managed virtual environment, run `python manage.py migrate`, and run `python manage.py collectstatic --noinput`.

Set `DJANGO_DEBUG=false`, a unique `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, SMTP settings, and a durable writable database path in the host's environment settings. Do not commit secrets. Configure a scheduled task for appointment cleanup and keep database backups access-controlled because the database contains contact details.

Pico.css, Bootstrap Icons, Source Sans 3, and DM Serif Display are currently loaded from public CDNs. Review this third-party asset delivery with the clinic before launch and update the privacy notice accordingly, or vendor the assets locally.
