from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('maintenance', '0002_companysettings_position'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [

        # PredictiveRecord
        migrations.CreateModel(
            name='PredictiveRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('parameter', models.CharField(max_length=50, choices=[
                    ('Temperature','Temperature (°C)'),('Vibration','Vibration (mm/s)'),
                    ('Current','Current (A)'),('Voltage','Voltage (V)'),
                    ('Pressure','Pressure (bar)'),('RPM','Speed (RPM)'),
                    ('Oil Level','Oil Level (%)'),('Noise','Noise Level (dB)'),
                    ('Humidity','Humidity (%)'),('Power','Power (kW)'),('Other','Other'),
                ])),
                ('value', models.DecimalField(max_digits=10, decimal_places=2)),
                ('unit', models.CharField(max_length=20, blank=True)),
                ('normal_min', models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)),
                ('normal_max', models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)),
                ('condition', models.CharField(max_length=20, default='Good', choices=[
                    ('Good','Good'),('Warning','Warning'),('Critical','Critical'),('Failed','Failed'),
                ])),
                ('notes', models.TextField(blank=True)),
                ('recorded_by', models.CharField(max_length=100, blank=True)),
                ('recorded_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                    related_name='predictive_records', to='maintenance.asset')),
            ],
            options={'ordering': ['-recorded_at']},
        ),

        # ProactiveAction
        migrations.CreateModel(
            name='ProactiveAction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=200)),
                ('action_type', models.CharField(max_length=50, choices=[
                    ('Lubrication','Lubrication'),('Alignment','Alignment'),
                    ('Belt Replacement','Belt Replacement'),('Filter Change','Filter Change'),
                    ('Calibration','Calibration'),('Cleaning','Cleaning'),
                    ('Tightening','Tightening'),('Adjustment','Adjustment'),
                    ('Part Replacement','Part Replacement'),('Inspection','Inspection'),('Other','Other'),
                ])),
                ('priority', models.CharField(max_length=20, default='Medium', choices=[
                    ('Critical','Critical'),('High','High'),('Medium','Medium'),('Low','Low'),
                ])),
                ('status', models.CharField(max_length=20, default='Planned', choices=[
                    ('Planned','Planned'),('In Progress','In Progress'),
                    ('Completed','Completed'),('Cancelled','Cancelled'),
                ])),
                ('trigger_reason', models.TextField()),
                ('action_plan', models.TextField(blank=True)),
                ('assigned_to', models.CharField(max_length=100, blank=True)),
                ('planned_date', models.DateField()),
                ('completed_date', models.DateField(null=True, blank=True)),
                ('estimated_hours', models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)),
                ('actual_hours', models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)),
                ('result', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                    related_name='proactive_actions', to='maintenance.asset')),
                ('created_by', models.ForeignKey(null=True, blank=True,
                    on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['planned_date']},
        ),

        # BreakdownAnalysis
        migrations.CreateModel(
            name='BreakdownAnalysis',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=200)),
                ('failure_date', models.DateField()),
                ('restored_date', models.DateField(null=True, blank=True)),
                ('total_downtime', models.DecimalField(max_digits=8, decimal_places=1, null=True, blank=True)),
                ('production_loss', models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)),
                ('repair_cost', models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)),
                ('cause_category', models.CharField(max_length=30, choices=[
                    ('Mechanical','Mechanical Failure'),('Electrical','Electrical Failure'),
                    ('Operational','Operational Error'),('Design','Design Deficiency'),
                    ('Maintenance','Maintenance Error'),('External','External Factor'),
                    ('Wear','Normal Wear & Tear'),('Unknown','Unknown'),
                ])),
                ('analysis_method', models.CharField(max_length=20, default='5-Why', choices=[
                    ('5-Why','5-Why Analysis'),('Fishbone','Fishbone (Ishikawa)'),
                    ('FMEA','FMEA'),('RCA','Root Cause Analysis'),('Other','Other'),
                ])),
                ('why_1', models.TextField(blank=True)),
                ('why_2', models.TextField(blank=True)),
                ('why_3', models.TextField(blank=True)),
                ('why_4', models.TextField(blank=True)),
                ('why_5', models.TextField(blank=True)),
                ('root_cause', models.TextField()),
                ('corrective_actions', models.TextField()),
                ('preventive_actions', models.TextField(blank=True)),
                ('lessons_learned', models.TextField(blank=True)),
                ('recurrence_risk', models.CharField(max_length=10, default='Medium', choices=[
                    ('High','High'),('Medium','Medium'),('Low','Low'),
                ])),
                ('analysed_by', models.CharField(max_length=100, blank=True)),
                ('approved_by', models.CharField(max_length=100, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                    related_name='breakdown_analyses', to='maintenance.asset')),
                ('work_order', models.OneToOneField(null=True, blank=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='breakdown_analysis', to='maintenance.workorder')),
                ('work_request', models.ForeignKey(null=True, blank=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='analyses', to='maintenance.workrequest')),
            ],
            options={'ordering': ['-failure_date'],
                     'verbose_name': 'Breakdown Analysis',
                     'verbose_name_plural': 'Breakdown Analyses'},
        ),

        # Facility
        migrations.CreateModel(
            name='Facility',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('code', models.CharField(max_length=20, unique=True)),
                ('name', models.CharField(max_length=200)),
                ('name_ar', models.CharField(max_length=200, blank=True)),
                ('facility_type', models.CharField(max_length=30, choices=[
                    ('Building','Building'),('Floor','Floor'),('Hall','Production Hall'),
                    ('Zone','Zone / Area'),('Substation','Electrical Substation'),
                    ('Utility Room','Utility Room'),('Warehouse','Warehouse'),
                    ('Office','Office'),('Outdoor','Outdoor Area'),('Other','Other'),
                ])),
                ('status', models.CharField(max_length=30, default='Active', choices=[
                    ('Active','Active / In Use'),('Under Renovation','Under Renovation'),('Closed','Closed'),
                ])),
                ('area_sqm', models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)),
                ('responsible_person', models.CharField(max_length=100, blank=True)),
                ('phone', models.CharField(max_length=30, blank=True)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('parent', models.ForeignKey(null=True, blank=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='sub_facilities', to='maintenance.facility')),
            ],
            options={'ordering': ['code'], 'verbose_name_plural': 'Facilities'},
        ),

        # FacilityServiceRequest
        migrations.CreateModel(
            name='FacilityServiceRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('sr_number', models.CharField(max_length=20, unique=True, editable=False)),
                ('category', models.CharField(max_length=30, choices=[
                    ('Civil','Civil / Construction'),('Electrical','Electrical'),
                    ('Plumbing','Plumbing'),('HVAC','HVAC / Air Conditioning'),
                    ('Cleaning','Cleaning / Housekeeping'),('Security','Security'),
                    ('IT','IT / Network'),('Fire Safety','Fire Safety'),
                    ('Pest Control','Pest Control'),('Other','Other'),
                ])),
                ('priority', models.CharField(max_length=20, default='Medium', choices=[
                    ('Urgent','Urgent'),('High','High'),('Medium','Medium'),('Low','Low'),
                ])),
                ('status', models.CharField(max_length=20, default='Open', choices=[
                    ('Open','Open'),('In Progress','In Progress'),
                    ('Completed','Completed'),('Rejected','Rejected'),
                ])),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('reported_by', models.CharField(max_length=100)),
                ('reporter_phone', models.CharField(max_length=30, blank=True)),
                ('assigned_to', models.CharField(max_length=100, blank=True)),
                ('due_date', models.DateField(null=True, blank=True)),
                ('completed_date', models.DateField(null=True, blank=True)),
                ('cost', models.DecimalField(max_digits=10, decimal_places=2, default=0)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('facility', models.ForeignKey(null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='service_requests', to='maintenance.facility')),
                ('created_by', models.ForeignKey(null=True, blank=True,
                    on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
