# Integration Handoff

## Backend and frontend

- Project folder: workspace root (Django SSR monolith).
- Install: `python -m pip install -r requirements.txt`.
- Migrate: `python manage.py migrate` (initial schema in `clinic/migrations/`).
- Run: `python manage.py runserver` (default port 8000).
- Build/check: `python manage.py check`.
- Tests: `python -m pytest`.
- Smoke-test the public GET routes and staff-admin redirect below; booking stays disabled until SMTP, privacy approval, and retention settings are present.
- Frontend: Django templates in `clinic/templates/`; static CSS/JS in `clinic/static/`.
- Staff: `python manage.py createsuperuser`; protected schedule and booking management at `/staff/`.
- API seam, mock client, and mock data: none; Django SSR with a database-backed appointment workflow.

## API route inventory

- `GET /` — home page.
- `GET /about` — clinic profile.
- `GET /services` — service directory.
- `GET /patient-information` — visitor information.
- `GET /contact` — verified contact information; no submission form.
- `GET /appointments` — booking page; form appears only after configuration and when slots exist.
- `POST /appointments` — validate visitor details/consent and reserve an available slot; email visitor and clinic.
- `GET /privacy` — privacy information.
- `GET /staff/` — protected Django admin login and management.

## Data and services

- Database: SQLite by default (`DJANGO_DATABASE_PATH`); schema managed by Django migrations. Verify a durable database option and filesystem permissions with cPanel before production. Migration `0002_approved_services` seeds only the three clinic-approved services; no appointment slots are seeded.
- Appointment retention: `APPOINTMENT_RETENTION_DAYS`; run `python manage.py purge_expired_appointments` on a scheduled task.
- Email: host SMTP via `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`, and `APPOINTMENT_NOTIFICATION_EMAIL`. Never commit credentials.
- Booking activation gate: `APPOINTMENT_PRIVACY_APPROVED=true`, positive retention, configured SMTP, active clinic services, and future slots. The form collects name/phone/email/branch/specialty preference/service/date/time/consent and optional practical logistics notes. Notes are visible only to staff in the dashboard/admin, excluded from email, and retained under the configured appointment-retention policy. Do not collect symptoms, diagnoses, or medical history.
- Azure Blob Storage: optional Enhancement only; unused by the current implementation. Local approved assets belong in Django static files.
- No public API, symptoms, medical history, patient documents, or contact-form submissions.
- Keep clinic facts not confirmed by the plan unpublished.
