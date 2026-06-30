from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [

        # ── ASSET ──────────────────────────────────────────
        migrations.CreateModel(
            name='Asset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('asset_id', models.CharField(max_length=50, unique=True)),
                ('name', models.CharField(max_length=200)),
                ('category', models.CharField(max_length=50, choices=[
                    ('Electrical','Electrical'),('Mechanical','Mechanical'),
                    ('Automation/PLC','Automation/PLC'),('HVAC','HVAC'),
                    ('Hydraulic','Hydraulic'),('Conveyor','Conveyor'),('Other','Other'),
                ])),
                ('location', models.CharField(max_length=200)),
                ('status', models.CharField(max_length=50, default='Operational', choices=[
                    ('Operational','Operational'),('Under Maintenance','Under Maintenance'),('Offline','Offline'),
                ])),
                ('manufacturer', models.CharField(max_length=100, blank=True)),
                ('model_number', models.CharField(max_length=100, blank=True)),
                ('serial_number', models.CharField(max_length=100, blank=True)),
                ('purchase_date', models.DateField(null=True, blank=True)),
                ('last_pm_date', models.DateField(null=True, blank=True)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['asset_id']},
        ),

        # ── WORK ORDER ─────────────────────────────────────
        migrations.CreateModel(
            name='WorkOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('wo_number', models.CharField(max_length=20, unique=True, editable=False)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('wo_type', models.CharField(max_length=50, default='Corrective', choices=[
                    ('Corrective','Corrective'),('Preventive','Preventive'),
                    ('Emergency','Emergency'),('Inspection','Inspection'),
                ])),
                ('priority', models.CharField(max_length=20, default='Medium', choices=[
                    ('Critical','Critical'),('Medium','Medium'),('Low','Low'),
                ])),
                ('status', models.CharField(max_length=20, default='Open', choices=[
                    ('Open','Open'),('In Progress','In Progress'),('On Hold','On Hold'),
                    ('Completed','Completed'),('Cancelled','Cancelled'),
                ])),
                ('assigned_to', models.CharField(max_length=100, blank=True)),
                ('due_date', models.DateField(null=True, blank=True)),
                ('completed_date', models.DateField(null=True, blank=True)),
                ('estimated_hours', models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)),
                ('actual_hours', models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)),
                ('parts_cost', models.DecimalField(max_digits=10, decimal_places=2, default=0)),
                ('labor_cost', models.DecimalField(max_digits=10, decimal_places=2, default=0)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('asset', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='work_orders', to='maintenance.asset')),
                ('created_by', models.ForeignKey(null=True, blank=True,
                    on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),

        # ── PM SCHEDULE ────────────────────────────────────
        migrations.CreateModel(
            name='PMSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('task_name', models.CharField(max_length=200)),
                ('frequency', models.CharField(max_length=20, choices=[
                    ('Daily','Daily'),('Weekly','Weekly'),('Monthly','Monthly'),
                    ('Quarterly','Quarterly'),('Semi-Annual','Semi-Annual'),('Annual','Annual'),
                ])),
                ('next_due', models.DateField()),
                ('assigned_to', models.CharField(max_length=100, blank=True)),
                ('estimated_hours', models.DecimalField(max_digits=4, decimal_places=1, default=1.0)),
                ('instructions', models.TextField(blank=True)),
                ('status', models.CharField(max_length=20, default='Active', choices=[
                    ('Active','Active'),('Inactive','Inactive'),
                ])),
                ('last_completed', models.DateField(null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                    related_name='pm_schedules', to='maintenance.asset')),
            ],
            options={'ordering': ['next_due']},
        ),

        # ── WORK REQUEST ───────────────────────────────────
        migrations.CreateModel(
            name='WorkRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('wr_number', models.CharField(max_length=20, unique=True, editable=False)),
                ('title', models.CharField(max_length=200)),
                ('location', models.CharField(max_length=200, blank=True)),
                ('alarm_type', models.CharField(max_length=50, choices=[
                    ('Electrical Fault','Electrical Fault'),('Mechanical Failure','Mechanical Failure'),
                    ('PLC/Automation Fault','PLC/Automation Fault'),('Overheat','Overheat'),
                    ('Vibration','Vibration'),('Noise/Sound','Noise/Sound'),('Leakage','Leakage'),
                    ('Production Stop','Production Stop'),('Safety Hazard','Safety Hazard'),
                    ('Power Failure','Power Failure'),('Sensor Fault','Sensor Fault'),('Other','Other'),
                ])),
                ('alarm_code', models.CharField(max_length=100, blank=True)),
                ('breakdown_type', models.CharField(max_length=50, default='Full Breakdown', choices=[
                    ('Full Breakdown','Full Breakdown'),('Partial Breakdown','Partial Breakdown'),
                    ('Performance Loss','Performance Loss'),('No Breakdown','No Breakdown — Preventive'),
                ])),
                ('priority', models.CharField(max_length=20, default='Medium', choices=[
                    ('Critical','Critical'),('High','High'),('Medium','Medium'),('Low','Low'),
                ])),
                ('status', models.CharField(max_length=20, default='New', choices=[
                    ('New','New'),('Under Review','Under Review'),('Approved','Approved'),
                    ('Rejected','Rejected'),('Converted','Converted to WO'),
                ])),
                ('description', models.TextField()),
                ('symptoms', models.TextField(blank=True)),
                ('production_impact', models.TextField(blank=True)),
                ('reported_by', models.CharField(max_length=100)),
                ('reporter_phone', models.CharField(max_length=30, blank=True)),
                ('reporter_department', models.CharField(max_length=100, blank=True)),
                ('breakdown_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('downtime_hours', models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)),
                ('review_notes', models.TextField(blank=True)),
                ('reviewed_at', models.DateTimeField(null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('asset', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='work_requests', to='maintenance.asset')),
                ('converted_to_wo', models.OneToOneField(null=True, blank=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='work_request', to='maintenance.workorder')),
                ('created_by', models.ForeignKey(null=True, blank=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_requests', to=settings.AUTH_USER_MODEL)),
                ('reviewed_by', models.ForeignKey(null=True, blank=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='reviewed_requests', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),

        # ── SPARE PART USAGE ───────────────────────────────
        migrations.CreateModel(
            name='SparePartUsage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('part_name', models.CharField(max_length=200)),
                ('part_number', models.CharField(max_length=100, blank=True)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('unit_cost', models.DecimalField(max_digits=10, decimal_places=2, default=0)),
                ('work_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                    related_name='parts', to='maintenance.workorder')),
            ],
        ),

        # ── USER PROFILE ───────────────────────────────────
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('role', models.CharField(max_length=30, default='technician', choices=[
                    ('admin','Administrator'),('section_head','Section Head'),
                    ('engineer','Maintenance Engineer'),('technician','Technician'),
                    ('operator','Operator'),('viewer','Viewer (Read Only)'),
                ])),
                ('employee_id', models.CharField(max_length=50, blank=True)),
                ('department', models.CharField(max_length=100, blank=True)),
                ('phone', models.CharField(max_length=30, blank=True)),
                ('photo', models.CharField(max_length=200, blank=True)),
                ('is_active', models.BooleanField(default=True)),
                # Page access
                ('can_access_dashboard',   models.BooleanField(default=True)),
                ('can_access_assets',      models.BooleanField(default=False)),
                ('can_access_workrequest', models.BooleanField(default=False)),
                ('can_access_workorder',   models.BooleanField(default=False)),
                ('can_access_pm',          models.BooleanField(default=False)),
                ('can_access_reports',     models.BooleanField(default=False)),
                # Action permissions
                ('can_create_wr',      models.BooleanField(default=False)),
                ('can_convert_wr',     models.BooleanField(default=False)),
                ('can_create_wo',      models.BooleanField(default=False)),
                ('can_close_wo',       models.BooleanField(default=False)),
                ('can_manage_assets',  models.BooleanField(default=False)),
                ('can_manage_pm',      models.BooleanField(default=False)),
                # Notification preferences
                ('notify_wr_new',       models.BooleanField(default=False)),
                ('notify_wr_converted', models.BooleanField(default=False)),
                ('notify_wr_rejected',  models.BooleanField(default=False)),
                ('notify_wo_assigned',  models.BooleanField(default=False)),
                ('notify_wo_completed', models.BooleanField(default=False)),
                ('notify_wo_overdue',   models.BooleanField(default=False)),
                ('notify_pm_due',       models.BooleanField(default=False)),
                ('notify_pm_overdue',   models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,
                    related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['user__username']},
        ),

        # ── NOTIFICATION ───────────────────────────────────
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('notif_type', models.CharField(max_length=30, choices=[
                    ('wr_new','New Work Request'),('wr_converted','Work Request Converted to WO'),
                    ('wo_assigned','Work Order Assigned'),('wo_completed','Work Order Completed'),
                    ('wo_overdue','Work Order Overdue'),('pm_due','PM Task Due'),
                    ('pm_overdue','PM Task Overdue'),('wr_rejected','Work Request Rejected'),
                ])),
                ('priority', models.CharField(max_length=10, default='normal', choices=[
                    ('critical','Critical'),('high','High'),('normal','Normal'),('low','Low'),
                ])),
                ('title', models.CharField(max_length=200)),
                ('message', models.TextField()),
                ('link', models.CharField(max_length=300, blank=True)),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                    related_name='notifications', to=settings.AUTH_USER_MODEL)),
                ('work_request', models.ForeignKey(null=True, blank=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='notifications', to='maintenance.workrequest')),
                ('work_order', models.ForeignKey(null=True, blank=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='notifications', to='maintenance.workorder')),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
