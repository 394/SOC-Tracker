from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.CharField(choices=[("L1", "L1 Analyst"), ("L2", "L2 Analyst"), ("L3", "L3 Admin")], default="L1", max_length=2)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="profile", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="Alert",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("alert_id", models.CharField(editable=False, max_length=16, unique=True)),
                ("title", models.CharField(max_length=180)),
                ("description", models.TextField(blank=True)),
                ("source", models.CharField(default="Manual", max_length=80)),
                ("severity", models.CharField(choices=[("Critical", "Critical"), ("High", "High"), ("Medium", "Medium"), ("Low", "Low")], default="Medium", max_length=10)),
                ("status", models.CharField(choices=[("New", "New"), ("Triage", "Triage"), ("Investigating", "Investigating"), ("Escalated", "Escalated"), ("Contained", "Contained"), ("Closed", "Closed")], default="New", max_length=20)),
                ("analyst", models.CharField(default="Unassigned", max_length=80)),
                ("tactic", models.CharField(default="Unknown", max_length=100)),
                ("asset", models.CharField(default="Unknown", max_length=160)),
                ("iocs", models.JSONField(blank=True, default=list)),
                ("sla_hours", models.PositiveIntegerField(default=8)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_alerts", to=settings.AUTH_USER_MODEL)),
                ("escalated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="escalated_alerts", to=settings.AUTH_USER_MODEL)),
                ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="updated_alerts", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
