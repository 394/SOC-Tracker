from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("alerts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="alert",
            name="assigned_to",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assigned_alerts", to=settings.AUTH_USER_MODEL),
        ),
    ]
