#!/usr/bin/env python
"""
Assetdigit CMMS — First Time Setup Script
Run this ONLY ONCE when installing for the first time.
After that, use: python manage.py runserver
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cmms.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from django.core.management import call_command
call_command('migrate')

from django.contrib.auth.models import User
from maintenance.models import UserProfile, CompanySettings

# ── Create admin user ONLY if it doesn't exist ────────────────────────────
if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser('admin', 'admin@cmms.local', 'admin123')
    admin.first_name = 'System'
    admin.last_name  = 'Administrator'
    admin.save()
    print("✅ Admin user created: admin / admin123")

    profile, _ = UserProfile.objects.get_or_create(user=admin)
    profile.role = 'admin'
    profile.apply_role_defaults()
    profile.notify_wr_new       = True
    profile.notify_wr_converted = True
    profile.notify_wr_rejected  = True
    profile.notify_wo_assigned  = True
    profile.notify_wo_completed = True
    profile.notify_wo_overdue   = True
    profile.notify_pm_due       = True
    profile.notify_pm_overdue   = True
    profile.save()
    print("✅ Admin profile created with full access + all notifications")
else:
    print("ℹ️  Admin user already exists — no changes made")

# ── Create default company settings ONLY if not set ──────────────────────
company = CompanySettings.get()
if company.factory_name == 'My Factory':
    company.factory_name = 'My Factory'
    company.logo_text    = '🏭'
    company.save()
    print("ℹ️  Default company settings ready — update from Company Settings page")
else:
    print(f"ℹ️  Company settings already configured: {company.factory_name}")

print("\n" + "="*55)
print("✅ Assetdigit CMMS Setup Complete!")
print("="*55)
print("  ▶  Start server : python manage.py runserver")
print("  🌐  Open browser : http://127.0.0.1:8000")
print("  🔑  Login        : admin / admin123")
print("="*55)
print("\n⚠️  IMPORTANT:")
print("  After this first setup, ONLY run:")
print("  python manage.py runserver")
print("  Your data is stored in cmms.db — backup it regularly!")
print("="*55)
