from django.db import migrations

APPROVED_SERVICES = (
    "General practice",
    "Outpatient care",
    "Laboratory",
)


def add_approved_services(apps, schema_editor):
    service_model = apps.get_model("clinic", "Service")
    database = schema_editor.connection.alias
    for name in APPROVED_SERVICES:
        service_model.objects.using(database).get_or_create(
            name=name,
            defaults={"description": "", "is_active": True},
        )


class Migration(migrations.Migration):
    dependencies = [("clinic", "0001_initial")]

    operations = [
        migrations.RunPython(add_approved_services, migrations.RunPython.noop)
    ]
