from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse


class UserProfile(models.Model):
    class Role(models.TextChoices):
        L1 = "L1", "L1 Analyst"
        L2 = "L2", "L2 Analyst"
        L3 = "L3", "L3 Admin"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=2, choices=Role.choices, default=Role.L1)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class Alert(models.Model):
    class Severity(models.TextChoices):
        CRITICAL = "Critical", "Critical"
        HIGH = "High", "High"
        MEDIUM = "Medium", "Medium"
        LOW = "Low", "Low"

    class Status(models.TextChoices):
        NEW = "New", "New"
        TRIAGE = "Triage", "Triage"
        INVESTIGATING = "Investigating", "Investigating"
        ESCALATED = "Escalated", "Escalated"
        CONTAINED = "Contained", "Contained"
        CLOSED = "Closed", "Closed"

    alert_id = models.CharField(max_length=16, unique=True, editable=False)
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    source = models.CharField(max_length=80, default="Manual")
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.MEDIUM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    analyst = models.CharField(max_length=80, default="Unassigned")
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_alerts")
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_alerts_made")
    tactic = models.CharField(max_length=100, default="Unknown")
    asset = models.CharField(max_length=160, default="Unknown")
    iocs = models.JSONField(default=list, blank=True)
    sla_hours = models.PositiveIntegerField(default=8)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="created_alerts")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="updated_alerts")
    escalated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="escalated_alerts")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.alert_id:
            last = Alert.objects.order_by("-id").first()
            next_number = (last.id if last else 0) + 1
            self.alert_id = f"SOC-{next_number:06d}"
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("alert_detail", args=[self.pk])

    def __str__(self):
        return f"{self.alert_id} {self.title}"


class AlertEvent(models.Model):
    class EventType(models.TextChoices):
        CREATED = "created", "Created"
        UPDATED = "updated", "Updated"
        ESCALATED = "escalated", "Escalated"
        ASSIGNED = "assigned", "Assigned"
        N8N_LOG = "n8n_log", "n8n Log"
        DELETED = "deleted", "Deleted"

    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    message = models.TextField()
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="alert_events")
    assigned_from = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="assignment_events_from")
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="assignment_events_to")
    source = models.CharField(max_length=80, default="tracker")
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.alert.alert_id} {self.event_type}"


@receiver(post_save, sender=User)
def ensure_profile(sender, instance, created, **kwargs):
    UserProfile.objects.get_or_create(user=instance)
