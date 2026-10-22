from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("clinic", "0004_appointment_branch")]

    operations = [
        migrations.AddField(
            model_name="appointment",
            name="specialty",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="appointment",
            name="notes",
            field=models.CharField(blank=True, max_length=500),
        ),
    ]
