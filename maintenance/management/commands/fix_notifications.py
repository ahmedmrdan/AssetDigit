"""
One-time fix: turn on sensible notification defaults for ALL existing users
based on their current role, WITHOUT touching any assets, work orders,
work requests, or any other data.

Run once:
    python manage.py fix_notifications
"""
from django.core.management.base import BaseCommand
from maintenance.models import UserProfile


class Command(BaseCommand):
    help = "Fix missing notification preferences for existing users (safe, one-time)"

    def handle(self, *args, **options):
        profiles = UserProfile.objects.all()
        count = 0
        for profile in profiles:
            before = (profile.notify_wr_new, profile.notify_wr_converted,
                      profile.notify_wo_assigned, profile.notify_wo_completed)
            # Re-apply role defaults — this ONLY changes permission/notification
            # booleans on the UserProfile, never touches Asset/WorkOrder/WorkRequest data
            profile.apply_role_defaults()
            profile.save()
            count += 1
            self.stdout.write(self.style.SUCCESS(
                f"✅ Updated notification defaults for: {profile.user.username} ({profile.role})"
            ))

        self.stdout.write(self.style.SUCCESS(
            f"\n🎉 Done! Fixed notification preferences for {count} user(s)."
        ))
        self.stdout.write(
            "ℹ️  No assets, work orders, or work requests were touched."
        )
