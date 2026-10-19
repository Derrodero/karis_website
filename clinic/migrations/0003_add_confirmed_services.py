from django.db import migrations

ADDITIONAL_SERVICES = (
    "Pharmacy",
    "Maternity and child health services",
    "Emergency and referral services",
)


def add_additional_services(apps, schema_editor):
    service_model = apps.get_model("clinic", "Service")
    database = schema_editor.connection.alias
    for name in ADDITIONAL_SERVICES:
        service_model.objects.using(database).get_or_create(
            name=name,
            defaults={"description": "", "is_active": True},
        )


class Migration(migrations.Migration):
    dependencies = [("clinic", "0002_approved_services")]

    operations = [
        migrations.RunPython(add_additional_services, migrations.RunPython.noop)
    ]
