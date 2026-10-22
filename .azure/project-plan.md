# Project Plan

**Status**: Awaiting Integration
**Created**: 2026-10-18
**Mode**: NEW

---

## 1. Project Overview

**Goal**: Build an original, accessible, server-rendered Django website for Karis Medical in Uganda, hosted through the user's cPanel account. Use verified clinic facts and the Karis logo when its file is supplied; Mayo Clinic is not a source for branding, copy, layouts, or assets. Keep unknown facts unpublished. Add admin-managed appointment slots with one confirmed booking per slot and clinic email notifications. Keep booking disabled until SMTP, clinic privacy approval, and a positive retention period are configured.

**App Type**: Full-stack SSR

**API Login**: No

**Mode**: NEW

**Deployment Plan**: No deployment plan found; user plans to deploy through cPanel

---

## 2. Karis Medical Django Website — backend

| Component | Technology |
|-----------|-----------|
| **Language** | Python |
| **Framework** | Django 5.2 LTS with server-rendered templates |
| **Runtime** | CPython |
| **Package Manager** | pip |
| **Test Runner** | pytest + pytest-django |
| **Mocking Library** | unittest.mock |
| **Test Command** | python -m pytest |
| **Orchestration** | docker-compose |
| **Database** | SQLite locally; verify durable database support with cPanel before production |

---

## 3. Services Required

| Azure Service | Role in App | Environment Variable | Default Value (Local) | Classification |
|---------------|------------|---------------------|----------------------|----------------|
| Blob Storage | Optional external origin for clinic-approved public media. Keep the supplied logo and approved site images in Django static files by default; no uploads, patient files, or Azure provisioning are in scope. | `PUBLIC_MEDIA_BASE_URL` | Empty; use local static files | Enhancement |

No public application API, symptoms, medical history, or Azure provisioning is in scope. Appointment records contain name, phone, email, selected branch, specialty preference, service/time, optional practical logistics notes, consent time, status, and a reference. Notes are restricted to appointment logistics, visible only to staff, excluded from email, and deleted under the configured appointment retention period. Staff manage services and slots through Django admin. SMTP delivery, clinic-approved privacy wording, and a positive retention period are required before public booking is enabled.

---

## 4. Prerequisites

Verify every `❓` tool before running locally. Confirm that the selected cPanel plan supports the required Python version, Django/WSGI application setup (Passenger or the host's supported equivalent), a durable database, SMTP, and static-file serving before deployment. No hosting credentials or paid-resource changes are part of planning.

### Run

| Tool | Service(s) | Installed | Version |
|------|------------|-----------|---------|
| Python | karis-web | ✅ | 3.12.10 |
| pip | karis-web | ❓ | unknown |

### Debug

| Tool | Service(s) | Installed | Version |
|------|------------|-----------|---------|
| Chrome | karis-web | ✅ | 145.0.7632.76 |

---

## 5. Design System & UI

**Component Library**: Pico.css
**Style Direction**: An original, calm clinic-information site using the approved Karis colors: clear navy wordmark, bright blue primary actions, and restrained red accents. The logo file is not yet present; keep the text wordmark until supplied. Keep navigation compact, content readable, and unknown clinic facts visibly unpublished until verified; avoid medical outcome claims and any borrowed Mayo Clinic identity or copy.
**Typography**: Source Sans 3 for headings and body, with Segoe UI Variable as a local fallback

### Color Palette

| Token | Hex | Usage |
|-------|-----|-------|
| `primary` | `#3288F7` | Links, primary actions, and active navigation drawn from the supplied logo's blue mark |
| `accent` | `#E51B23` | Restrained highlights and alert accents drawn from the supplied logo's red mark |
| `surface` | `#F7F8FC` | Public page background and quiet content areas |
| `text` | `#24205B` | High-contrast headings and brand wordmark tone |
| `muted` | `#66677D` | Supporting labels and verification notes |
| `border` | `#DEE1EC` | Dividers and restrained control outlines |

### Pages

| Page | Route | Purpose | Layout |
|------|-------|---------|--------|
| Home | `/` | Identify Karis Medical and publish the two confirmed branches, opening hours, and approved services. | `header, nav, hero, grid, branch list, footer` |
| About Karis | `/about` | Present the April 2025 founding, mission, vision, values, facilities, outreach priorities, and verified team information. | `header, nav, main, overview, sections, footer` |
| Services | `/services` | List general practice, outpatient care, laboratory, pharmacy, maternity/child health, and emergency/referral services without unverified claims. | `header, nav, main, list, footer` |
| Patient Information | `/patient-information` | Publish both verified Kampala branch locations and 24/7 hours; do not invent clinical or emergency guidance. | `header, nav, main, branch list, footer` |
| Contact | `/contact` | Provide the two verified branch phone numbers and addresses; contact links do not book or confirm appointments. | `header, nav, main, branch list, footer` |
| Appointments | `/appointments` | Book one clinic-administered future slot and email confirmation to visitor and clinic when configured. | `header, nav, main, form, privacy notice, footer` |
| Privacy | `/privacy` | Explain public-site and appointment data handling; booking stays disabled until policy approval. | `header, nav, main, list, footer` |

### Sample Content

Home — public clinic facts:
| Fact | Value | Publication state |
|------|-------|-------------------|
| Clinic name | Karis Medical | Confirmed |
| Country | Uganda | Confirmed |
| Kyanja branch | Westmall, Kisasi Road, Kyanja, Kampala, Uganda; 039 300 1567 | Confirmed |
| Naalya branch | Ground Floor, Naalya Heights, Naalya-Namugongo Road, Kampala, Uganda; 039 310 4667 | Confirmed |
| Opening hours | 24 hours, Monday through Sunday | Confirmed |

About Karis — profile details:
| Detail | Value | Publication state |
|--------|-------|-------------------|
| Organization and location | Karis Medical, Kyanja and Naalya branches in Kampala, Uganda | Confirmed |
| Established | April 2025 | Confirmed |
| Slogan | Beyond care. | Confirmed |
| Supporting line | Compassionate care and a healthier community. | Confirmed |
| Mission | To glorify God through healthcare. | Confirmed |
| Vision | To be the health care provider of choice for all Ugandans. | Confirmed |
| Core values | Compassion, integrity, hospitality, professionalism, respect, teamwork, patient safety | Confirmed |
| Founding story | Original summary based on the supplied founding date, mission, and vision | Published; further milestones pending verification |
| Patient-growth and testimonial metrics | No verified figures supplied | Unpublished pending records and approval |
| Team names and professional credentials | Not supplied | Unpublished pending clinic verification |

Services — directory content:
| Record | Value | Publication state |
|--------|-------|-------------------|
| Clinic-approved service list | General practice; outpatient care; laboratory; pharmacy; maternity and child health; emergency and referral | Confirmed |
| Service descriptions | Not supplied | Unpublished pending clinic review |
| Eligibility, pricing, and availability | Not supplied | Unpublished pending verification |

Patient Information — visitor details:
| Record | Value | Publication state |
|--------|-------|-------------------|
| Clinic location and directions | Kyanja and Naalya branch addresses above | Confirmed |
| Opening hours | 24 hours, Monday through Sunday | Confirmed |
| Facilities | Outpatient and consultation rooms; laboratory and diagnostic services; pharmacy; maternity and child health; emergency and referral services | Confirmed by user |
| Visit preparation and accessibility details | Not supplied | Unpublished pending clinic confirmation |

Community outreach priorities:
| Programme | Publication state |
|-----------|-------------------|
| Health education, community screening, child health outreach, immunisation campaigns, organisation partnerships | Listed as clinic-provided priorities; dates, partners, and outcomes require verification |

Contact — approved channels:
| Channel | Value | Publication state |
|---------|-------|-------------------|
| Kyanja public telephone | 039 300 1567 | Confirmed |
| Naalya public telephone | 039 310 4667 | Confirmed |
| Public email | Not supplied | Unpublished pending verification |
| Appointment workflow | Admin-managed live slot booking, one active booking per slot, email confirmations | Approved; disabled pending clinic setup |

Privacy — launch data scope:
| Data practice | Value | Publication state |
|---------------|-------|-------------------|
| Appointment data | Name, phone, email, branch, specialty preference, service/time, optional practical notes, and consent timestamp; no symptoms or medical history | Approved fields; booking disabled pending policy configuration |
| Contact form submissions | Not in launch scope | Confirmed scope |
| Retention period and privacy notice wording | Not supplied | Booking remains disabled pending clinic approval |

---

## 6. Project Structure

```text
karis-medical/
├── .azure/
│   └── project-plan.md
├── manage.py
├── requirements.txt
├── passenger_wsgi.py                # cPanel/Passenger entry point, if supported by host
├── karis_site/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── clinic/
│   ├── models.py                   # Services, slots, and appointment records
│   ├── forms.py
│   ├── admin.py                    # Staff schedule and booking management
│   ├── views.py
│   ├── urls.py
│   ├── content.py                   # Verified public facts; no invented defaults
│   ├── templates/clinic/            # Server-rendered public pages
│   ├── static/clinic/css/
│   ├── migrations/
│   ├── management/commands/        # Appointment retention cleanup
│   └── tests/
└── static/
    └── clinic/images/               # Supplied logo and authorized clinic assets
```

---

## 7. Route Definitions

| # | Method | Path | Description | Request Body | Response Body | Status Codes |
|---|--------|------|-------------|-------------|--------------|-------------|
| 1 | GET | `/` | Public home page with only verified clinic facts | — | Server-rendered HTML | 200, 404 |
| 2 | GET | `/about` | Approved Karis background and authorized team information | — | Server-rendered HTML | 200, 404 |
| 3 | GET | `/services` | Clinic-approved service directory | — | Server-rendered HTML | 200, 404 |
| 4 | GET | `/patient-information` | Verified location, hours, and practical visit information | — | Server-rendered HTML | 200, 404 |
| 5 | GET | `/contact` | Verified contact channels; no appointment submission | — | Server-rendered HTML | 200, 404 |
| 6 | GET, POST | `/appointments` | Book an available clinic-approved slot; confirm by email when enabled | Name, phone, email, service, slot, consent | Server-rendered HTML | 200, 404 |
| 7 | GET | `/privacy` | Public-site and appointment data notice | — | Server-rendered HTML | 200, 404 |
| 8 | GET, POST | `/staff/` | Protected Django admin sign-in and service, slot, and booking management | Staff credentials / admin forms | Server-rendered HTML | 200, 302 |

No public application API routes are included. Django admin routes require staff authentication.

---

## 8. Next Steps

1. Provide the Karis logo file, social profile URLs, verified booking schedule, notification email, privacy wording, and retention period.
2. Configure SMTP and approved privacy/retention values before enabling public booking; create a staff superuser and add verified services and future slots.
3. Confirm cPanel support for Python/Django WSGI hosting, a durable writable database, SMTP, and static files before deployment.
4. Run `python manage.py migrate`, `python manage.py createsuperuser`, and schedule `python manage.py purge_expired_appointments` at the clinic-approved retention interval.
5. **azure-project-integrate** can verify migrations and configured booking flows; no public API wiring or seed data is needed.
6. Run **azure-debug-plan** → **azure-debug-generate** for local debugging configuration if needed. Select hosting and budget before running the **azure-deploy** agent; this plan does not authorize Azure provisioning or deployment.
