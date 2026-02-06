from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("shop", "0005_callbackrequest"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="acknowledged_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="order",
            name="reminder_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
