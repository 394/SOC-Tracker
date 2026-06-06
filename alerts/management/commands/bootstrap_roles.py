from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from alerts.models import UserProfile


class Command(BaseCommand):
    help = "Create demo L1/L2/L3 users. Password for each user is password123."

    def handle(self, *args, **options):
        for username, role, is_staff, is_superuser in [
            ("l1", UserProfile.Role.L1, False, False),
            ("l2", UserProfile.Role.L2, False, False),
            ("admin_l3", UserProfile.Role.L3, True, True),
        ]:
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_password("password123")
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.save()
            user.profile.role = role
            user.profile.save()
            self.stdout.write(self.style.SUCCESS(f"{username}: {role}"))
