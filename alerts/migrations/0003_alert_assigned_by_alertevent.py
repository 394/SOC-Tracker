from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("alerts", "0002_alert_assigned_to"),
    ]

    operations = [
        migrations.AddField(
            model_name="alert",
            name="assigned_by",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assigned_alerts_made", to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name="AlertEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_type", models.CharField(choices=[("created", "Created"), ("updated", "Updated"), ("escalated", "Escalated"), ("assigned", "Assigned"), ("n8n_log", "n8n Log"), ("deleted", "Deleted")], max_length=20)),
                ("message", models.TextField()),
                ("source", models.CharField(default="tracker", max_length=80)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="alert_events", to=settings.AUTH_USER_MODEL)),
                ("alert", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="events", to="alerts.alert")),
                ("assigned_from", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assignment_events_from", to=settings.AUTH_USER_MODEL)),
                ("assigned_to", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assignment_events_to", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
