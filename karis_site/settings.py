import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env", override=True)

DEBUG = os.environ.get("DJANGO_DEBUG", "true").lower() in {"1", "true", "yes"}
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY must be set when DEBUG is disabled."
        )
    SECRET_KEY = "local-development-only-key-not-for-production"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        "DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver"
    ).split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "clinic",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "karis_site.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "karis_site.wsgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get("DJANGO_DATABASE_PATH") or BASE_DIR / "db.sqlite3",
        "OPTIONS": {"timeout": 20},
    }
}

LANGUAGE_CODE = "en"
TIME_ZONE = "Africa/Kampala"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

PUBLIC_MEDIA_BASE_URL = os.environ.get("PUBLIC_MEDIA_BASE_URL", "").rstrip("/")
APPEND_SLASH = False

EMAIL_HOST = os.environ.get("EMAIL_HOST", "").strip()
EMAIL_PORT = int(os.environ.get("EMAIL_PORT") or "587")
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "").strip()
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "").strip()
EMAIL_USE_TLS = (os.environ.get("EMAIL_USE_TLS") or "true").lower() in {
    "1",
    "true",
    "yes",
}
EMAIL_TIMEOUT = 10
DEFAULT_FROM_EMAIL = (
    os.environ.get("DEFAULT_FROM_EMAIL", "").strip()
    or EMAIL_HOST_USER
    or "help@karisclinic.com"
)
APPOINTMENT_NOTIFICATION_EMAIL = (
    os.environ.get("APPOINTMENT_NOTIFICATION_EMAIL", "").strip()
    or "help@karisclinic.com"
)
EMAIL_CONFIGURED = all((EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD))
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "").strip() or (
    "django.core.mail.backends.smtp.EmailBackend"
    if EMAIL_CONFIGURED
    else "django.core.mail.backends.console.EmailBackend"
)
APPOINTMENT_PRIVACY_APPROVED = (
    os.environ.get("APPOINTMENT_PRIVACY_APPROVED") or "true"
).lower() in {"1", "true", "yes"}

try:
    APPOINTMENT_RETENTION_DAYS = int(
        os.environ.get("APPOINTMENT_RETENTION_DAYS") or "90"
    )
except ValueError:
    APPOINTMENT_RETENTION_DAYS = 90

APPOINTMENTS_ENABLED = (
    (os.environ.get("APPOINTMENTS_ENABLED") or "true").lower() in {"1", "true", "yes"}
    and APPOINTMENT_PRIVACY_APPROVED
    and APPOINTMENT_RETENTION_DAYS > 0
)
