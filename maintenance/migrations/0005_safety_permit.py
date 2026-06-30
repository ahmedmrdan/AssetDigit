from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('maintenance', '0004_iso_modules'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # New UserProfile fields
        migrations.AddField(
            model_name='userprofile', name='notify_safety_permit',
            field=models.BooleanField(default=False, verbose_name='Notify: New Safety Permit needs approval'),
        ),
        migrations.AddField(
            model_name='userprofile', name='can_access_safety',
            field=models.BooleanField(default=False, verbose_name='Can Access Safety Permits'),
        ),
        migrations.AddField(
            model_name='userprofile', name='can_approve_safety',
            field=models.BooleanField(default=False, verbose_name='Can Approve/Reject Safety Permits'),
        ),

        # SafetyPermit model
        migrations.CreateModel(
            name='SafetyPermit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('permit_number', models.CharField(max_length=20, unique=True, editable=False)),
                ('permit_type', models.CharField(max_length=30, default='General', choices=[
                    ('General','General Work Permit'),
                    ('Hot Work','Hot Work Permit (Welding/Cutting/Grinding)'),
                    ('Confined Space','Confined Space Entry Permit'),
                    ('Electrical','Electrical Isolation / LOTO Permit'),
                    ('Working at Height','Working at Height Permit'),
                    ('Excavation','Excavation Permit'),
                    ('Lifting','Lifting Operation Permit'),
                    ('Chemical','Chemical Handling Permit'),
                    ('Other','Other'),
                ])),
                ('status', models.CharField(max_length=20, default='Pending', choices=[
                    ('Pending','Pending Approval'),('Approved','Approved — Work May Start'),
                    ('Active','Active — Work In Progress'),('Suspended','Suspended'),
                    ('Closed','Closed — Work Completed'),('Rejected','Rejected'),
                    ('Expired','Expired'),
                ])),
                ('risk_level', models.CharField(max_length=20, default='Medium', choices=[
                    ('Low','Low Risk'),('Medium','Medium Risk'),
                    ('High','High Risk'),('Critical','Critical Risk'),
                ])),
                ('work_description', models.TextField()),
                ('location', models.CharField(max_length=300, blank=True)),
                ('requested_by', models.CharField(max_length=100)),
                ('workers_involved', models.TextField(blank=True)),
                ('supervisor', models.CharField(max_length=100, blank=True)),
                ('approved_by', models.CharField(max_length=100, blank=True)),
                ('hazards_identified', models.TextField(blank=True)),
                ('ppe_required', models.TextField(blank=True)),
                ('precautions_taken', models.TextField(blank=True)),
                ('isolation_required', models.BooleanField(default=False)),
                ('isolation_details', models.TextField(blank=True)),
                ('fire_watch_required', models.BooleanField(default=False)),
                ('gas_test_required', models.BooleanField(default=False)),
                ('gas_test_result', models.CharField(max_length=200, blank=True)),
                ('valid_from', models.DateTimeField(default=django.utils.timezone.now)),
                ('valid_until', models.DateTimeField(null=True, blank=True)),
                ('approval_notes', models.TextField(blank=True)),
                ('rejection_reason', models.TextField(blank=True)),
                ('approved_at', models.DateTimeField(null=True, blank=True)),
                ('closed_by', models.CharField(max_length=100, blank=True)),
                ('closed_at', models.DateTimeField(null=True, blank=True)),
                ('closure_notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('work_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                    related_name='safety_permits', to='maintenance.workorder')),
                ('created_by', models.ForeignKey(null=True, blank=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_permits', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at'],
                     'verbose_name': 'Safety Permit',
                     'verbose_name_plural': 'Safety Permits'},
        ),
    ]
