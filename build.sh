#!/usr/bin/env bash
# Render Build Script — runs automatically on every deploy
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate --no-input

# Create the admin user automatically ONLY if it doesn't exist yet
# This NEVER touches existing data — safe to run on every deploy
python manage.py shell << 'PYEOF'
from django.contrib.auth.models import User
from maintenance.models import UserProfile, CompanySettings

if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser('admin', 'admin@cmms.local', 'admin123')
    admin.first_name = 'System'
    admin.last_name = 'Administrator'
    admin.save()
    profile, _ = UserProfile.objects.get_or_create(user=admin)
    profile.role = 'admin'
    profile.apply_role_defaults()
    profile.save()
    print("Admin user created: admin / admin123")
else:
    print("Admin user already exists - skipped (data preserved)")

CompanySettings.get()
print("Build script finished successfully")
PYEOF
