from datetime import timedelta

from django.conf import settings
from django.core.management import BaseCommand, CommandError
from django.utils import timezone

from clinic.models import Appointment


class Command(BaseCommand):
    help = (
        "Delete appointment contact details older than the configured retention period."
    )

    def handle(self, *args, **options):
        retention_days = settings.APPOINTMENT_RETENTION_DAYS
        if retention_days <= 0:
            raise CommandError("Set a positive APPOINTMENT_RETENTION_DAYS value first.")

        cutoff = timezone.now() - timedelta(days=retention_days)
        deleted, _ = Appointment.objects.filter(created_at__lt=cutoff).delete()
        self.stdout.write(f"Deleted {deleted} expired appointment records.")
