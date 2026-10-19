from django.contrib import admin
from django.urls import path
from django.views.generic.base import RedirectView

from clinic import views

handler404 = "clinic.views.page_not_found"

urlpatterns = [
    path("staff/login", views.staff_login, name="staff_login"),
    path("staff/logout", views.staff_logout, name="staff_logout"),
    path("staff/dashboard", views.staff_dashboard, name="staff_dashboard"),
    path(
        "staff/appointments/<int:pk>/status",
        views.staff_appointment_status,
        name="staff_appointment_status",
    ),
    path(
        "staff/slots/<int:pk>/toggle",
        views.staff_slot_toggle,
        name="staff_slot_toggle",
    ),
    path(
        "staff/services/<int:pk>/toggle",
        views.staff_service_toggle,
        name="staff_service_toggle",
    ),
    path("staff/", admin.site.urls),
    path("", views.home, name="home"),
    path("about", views.about, name="about"),
    path("services", views.services, name="services"),
    path(
        "patient-information",
        RedirectView.as_view(pattern_name="contact", permanent=True),
        name="patient_information",
    ),
    path("contact", views.contact, name="contact"),
    path("appointments", views.appointments, name="appointments"),
    path("privacy", views.privacy, name="privacy"),
]
