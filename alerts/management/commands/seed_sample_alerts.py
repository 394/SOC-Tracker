from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from alerts.models import Alert, AlertEvent


class Command(BaseCommand):
    help = "Create sample SOC alerts owned by L1 and L2 demo users."

    def handle(self, *args, **options):
        l1 = User.objects.get(username="l1")
        l2 = User.objects.get(username="l2")

        samples = [
            {
                "title": "L1 triage - suspicious VPN login",
                "description": "L1 identified an unusual VPN login from a new country for a finance user. MFA succeeded, but the source IP has poor reputation.",
                "source": "Elastic",
                "severity": Alert.Severity.HIGH,
                "status": Alert.Status.TRIAGE,
                "analyst": "l1",
                "tactic": "Initial Access",
                "asset": "finance.user@example.local",
                "iocs": ["198.51.100.77", "finance.user@example.local"],
                "sla_hours": 4,
                "created_by": l1,
                "updated_by": l1,
                "assigned_to": l1,
                "assigned_by": l1,
            },
            {
                "title": "L2 investigation - escalated PowerShell execution",
                "description": "L2 is investigating an L1-escalated encoded PowerShell command launched from a user Downloads directory.",
                "source": "Elastic EDR",
                "severity": Alert.Severity.CRITICAL,
                "status": Alert.Status.ESCALATED,
                "analyst": "l2",
                "tactic": "Execution",
                "asset": "WIN-ENG-044",
                "iocs": ["powershell.exe", "-EncodedCommand", "WIN-ENG-044"],
                "sla_hours": 2,
                "created_by": l1,
                "updated_by": l2,
                "escalated_by": l1,
                "assigned_to": l2,
                "assigned_by": l2,
            },
        ]

        for sample in samples:
            alert, created = Alert.objects.get_or_create(
                title=sample["title"],
                defaults=sample,
            )
            if not created:
                for field, value in sample.items():
                    setattr(alert, field, value)
                alert.save()
            AlertEvent.objects.get_or_create(
                alert=alert,
                event_type=AlertEvent.EventType.ASSIGNED,
                message=f"{sample['assigned_by'].username} assigned this alert to {sample['assigned_to'].username}.",
                defaults={
                    "actor": sample["assigned_by"],
                    "assigned_to": sample["assigned_to"],
                    "source": "seed",
                },
            )
            action = "created" if created else "exists"
            self.stdout.write(self.style.SUCCESS(f"{alert.alert_id}: {action}"))
