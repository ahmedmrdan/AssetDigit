from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Asset(models.Model):
    CATEGORY_CHOICES = [
        ('Electrical', 'Electrical'),
        ('Mechanical', 'Mechanical'),
        ('Automation/PLC', 'Automation/PLC'),
        ('HVAC', 'HVAC'),
        ('Hydraulic', 'Hydraulic'),
        ('Conveyor', 'Conveyor'),
        ('Other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('Operational', 'Operational'),
        ('Under Maintenance', 'Under Maintenance'),
        ('Offline', 'Offline'),
    ]

    asset_id   = models.CharField(max_length=50, unique=True)
    name       = models.CharField(max_length=200)
    category   = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    location   = models.CharField(max_length=200)
    status     = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Operational')
    manufacturer = models.CharField(max_length=100, blank=True)
    model_number = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    last_pm_date  = models.DateField(null=True, blank=True)
    notes      = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.asset_id} - {self.name}"

    class Meta:
        ordering = ['asset_id']


class WorkOrder(models.Model):
    PRIORITY_CHOICES = [
        ('Critical', 'Critical'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
    ]
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('In Progress', 'In Progress'),
        ('On Hold', 'On Hold'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]
    TYPE_CHOICES = [
        ('Corrective', 'Corrective'),
        ('Preventive', 'Preventive'),
        ('Emergency', 'Emergency'),
        ('Inspection', 'Inspection'),
    ]

    wo_number    = models.CharField(max_length=20, unique=True, editable=False)
    title        = models.CharField(max_length=200)
    description  = models.TextField(blank=True)
    asset        = models.ForeignKey(Asset, on_delete=models.SET_NULL, null=True, related_name='work_orders')
    wo_type      = models.CharField(max_length=50, choices=TYPE_CHOICES, default='Corrective')
    priority     = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Medium')
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    assigned_to  = models.CharField(max_length=100, blank=True)
    due_date     = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True,
                                        verbose_name='Completed At (exact timestamp)',
                                        help_text='Used to calculate actual cycle time')
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    actual_hours    = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    parts_cost   = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    labor_cost   = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes        = models.TextField(blank=True)
    created_by   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.wo_number:
            last = WorkOrder.objects.order_by('id').last()
            num = (last.id + 1) if last else 1
            self.wo_number = f"WO-{num:04d}"
        super().save(*args, **kwargs)

    def is_overdue(self):
        return self.due_date and self.due_date < timezone.now().date() and self.status not in ['Completed', 'Cancelled']

    def cycle_time_hours(self):
        """
        Actual time from WO creation to completion, in hours.
        Returns None if not yet completed.
        """
        if self.completed_at and self.created_at:
            delta = self.completed_at - self.created_at
            return round(delta.total_seconds() / 3600, 1)
        return None

    def cycle_time_display(self):
        """Human-friendly cycle time, e.g. '2d 4h' or '5h 30m'."""
        hours = self.cycle_time_hours()
        if hours is None:
            return None
        total_minutes = int(hours * 60)
        days, rem_minutes = divmod(total_minutes, 1440)
        hrs, mins = divmod(rem_minutes, 60)
        if days > 0:
            return f"{days}d {hrs}h"
        elif hrs > 0:
            return f"{hrs}h {mins}m"
        else:
            return f"{mins}m"

    def __str__(self):
        return f"{self.wo_number} - {self.title}"


    class Meta:
        ordering = ['-created_at']


class PMSchedule(models.Model):
    FREQUENCY_CHOICES = [
        ('Daily', 'Daily'),
        ('Weekly', 'Weekly'),
        ('Monthly', 'Monthly'),
        ('Quarterly', 'Quarterly'),
        ('Semi-Annual', 'Semi-Annual'),
        ('Annual', 'Annual'),
    ]
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]

    task_name    = models.CharField(max_length=200)
    asset        = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='pm_schedules')
    frequency    = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    next_due     = models.DateField()
    assigned_to  = models.CharField(max_length=100, blank=True)
    estimated_hours = models.DecimalField(max_digits=4, decimal_places=1, default=1.0)
    instructions = models.TextField(blank=True)
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    last_completed = models.DateField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    def is_overdue(self):
        return self.next_due < timezone.now().date() and self.status == 'Active'

    def __str__(self):
        return f"{self.task_name} - {self.asset.name}"

    class Meta:
        ordering = ['next_due']


class WorkRequest(models.Model):
    PRIORITY_CHOICES = [
        ('Critical', 'Critical'),
        ('High',     'High'),
        ('Medium',   'Medium'),
        ('Low',      'Low'),
    ]
    STATUS_CHOICES = [
        ('New',          'New'),
        ('Under Review', 'Under Review'),
        ('Approved',     'Approved'),
        ('Rejected',     'Rejected'),
        ('Converted',    'Converted to WO'),
    ]
    ALARM_TYPE_CHOICES = [
        ('Electrical Fault',    'Electrical Fault'),
        ('Mechanical Failure',  'Mechanical Failure'),
        ('PLC/Automation Fault','PLC/Automation Fault'),
        ('Overheat',            'Overheat'),
        ('Vibration',           'Vibration'),
        ('Noise/Sound',         'Noise/Sound'),
        ('Leakage',             'Leakage'),
        ('Production Stop',     'Production Stop'),
        ('Safety Hazard',       'Safety Hazard'),
        ('Power Failure',       'Power Failure'),
        ('Sensor Fault',        'Sensor Fault'),
        ('Other',               'Other'),
    ]
    BREAKDOWN_CHOICES = [
        ('Full Breakdown',    'Full Breakdown'),
        ('Partial Breakdown', 'Partial Breakdown'),
        ('Performance Loss',  'Performance Loss'),
        ('No Breakdown',      'No Breakdown — Preventive'),
    ]

    wr_number         = models.CharField(max_length=20, unique=True, editable=False)
    title             = models.CharField(max_length=200)
    asset             = models.ForeignKey(Asset, on_delete=models.SET_NULL, null=True, related_name='work_requests')
    location          = models.CharField(max_length=200, blank=True)
    alarm_type        = models.CharField(max_length=50, choices=ALARM_TYPE_CHOICES)
    alarm_code        = models.CharField(max_length=100, blank=True, help_text='Alarm/Error code shown on HMI or PLC')
    breakdown_type    = models.CharField(max_length=50, choices=BREAKDOWN_CHOICES, default='Full Breakdown')
    priority          = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Medium')
    status            = models.CharField(max_length=20, choices=STATUS_CHOICES, default='New')
    description       = models.TextField(help_text='Describe the problem in detail')
    symptoms          = models.TextField(blank=True, help_text='What symptoms are observed?')
    production_impact = models.TextField(blank=True, help_text='Impact on production / safety')
    reported_by       = models.CharField(max_length=100)
    reporter_phone    = models.CharField(max_length=30, blank=True)
    reporter_department = models.CharField(max_length=100, blank=True)
    breakdown_time    = models.DateTimeField(default=timezone.now, help_text='When did the breakdown occur?')
    downtime_hours    = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True, help_text='Estimated downtime in hours')

    # After conversion
    converted_to_wo   = models.OneToOneField('WorkOrder', on_delete=models.SET_NULL, null=True, blank=True, related_name='work_request')
    reviewed_by       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_requests')
    review_notes      = models.TextField(blank=True)
    reviewed_at       = models.DateTimeField(null=True, blank=True)

    created_by        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_requests')
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.wr_number:
            last = WorkRequest.objects.order_by('id').last()
            num = (last.id + 1) if last else 1
            self.wr_number = f"WR-{num:04d}"
        super().save(*args, **kwargs)

    def is_urgent(self):
        return self.priority in ['Critical', 'High']

    def __str__(self):
        return f"{self.wr_number} - {self.title}"

    class Meta:
        ordering = ['-created_at']


class SparePartUsage(models.Model):
    work_order   = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='parts')
    part_name    = models.CharField(max_length=200)
    part_number  = models.CharField(max_length=100, blank=True)
    quantity     = models.PositiveIntegerField(default=1)
    unit_cost    = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def total_cost(self):
        return self.quantity * self.unit_cost

    def __str__(self):
        return f"{self.part_name} x{self.quantity}"


class UserProfile(models.Model):
    """Extended profile for each user — stores access permissions."""

    ROLE_CHOICES = [
        ('admin',       'Administrator'),
        ('section_head','Section Head'),
        ('engineer',    'Maintenance Engineer'),
        ('technician',  'Technician'),
        ('operator',    'Operator'),
        ('viewer',      'Viewer (Read Only)'),
    ]

    user               = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role               = models.CharField(max_length=30, choices=ROLE_CHOICES, default='technician')
    employee_id        = models.CharField(max_length=50, blank=True)
    department         = models.CharField(max_length=100, blank=True)
    position           = models.CharField(max_length=100, blank=True, verbose_name='Job Position/Title',
                                          help_text='e.g. Senior Maintenance Engineer, Production Supervisor')
    phone              = models.CharField(max_length=30, blank=True)
    photo              = models.CharField(max_length=200, blank=True)  # initials fallback
    is_active          = models.BooleanField(default=True)

    # Page-level access permissions
    can_access_dashboard    = models.BooleanField(default=True)
    can_access_assets       = models.BooleanField(default=False)
    can_access_workrequest  = models.BooleanField(default=False)
    can_access_workorder    = models.BooleanField(default=False)
    can_access_pm           = models.BooleanField(default=False)
    can_access_reports      = models.BooleanField(default=False)

    # Action-level permissions
    can_create_wr      = models.BooleanField(default=False, verbose_name='Can Create Work Requests')
    can_convert_wr     = models.BooleanField(default=False, verbose_name='Can Convert WR → WO')
    can_create_wo      = models.BooleanField(default=False, verbose_name='Can Create Work Orders')
    can_close_wo       = models.BooleanField(default=False, verbose_name='Can Close/Complete WOs')
    can_manage_assets  = models.BooleanField(default=False, verbose_name='Can Add/Edit Assets')
    can_manage_pm      = models.BooleanField(default=False, verbose_name='Can Manage PM Schedule')

    # Notification preferences
    notify_wr_new       = models.BooleanField(default=False, verbose_name='Notify: New Work Request submitted')
    notify_wr_converted = models.BooleanField(default=False, verbose_name='Notify: Work Request converted to WO')
    notify_wr_rejected  = models.BooleanField(default=False, verbose_name='Notify: Work Request rejected')
    notify_wo_assigned  = models.BooleanField(default=False, verbose_name='Notify: Work Order assigned to me')
    notify_wo_completed = models.BooleanField(default=False, verbose_name='Notify: Work Order completed')
    notify_wo_overdue   = models.BooleanField(default=False, verbose_name='Notify: Work Order overdue')
    notify_pm_due       = models.BooleanField(default=False, verbose_name='Notify: PM Task due soon')
    notify_pm_overdue   = models.BooleanField(default=False, verbose_name='Notify: PM Task overdue')
    notify_safety_permit = models.BooleanField(default=False, verbose_name='Notify: New Safety Permit needs approval')

    # Safety module permissions
    can_access_safety   = models.BooleanField(default=False, verbose_name='Can Access Safety Permits')
    can_approve_safety  = models.BooleanField(default=False, verbose_name='Can Approve/Reject Safety Permits')

    created_at         = models.DateTimeField(auto_now_add=True)
    updated_at         = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"

    def apply_role_defaults(self):
        """Apply sensible default permissions based on selected role."""
        role = self.role
        # Reset all first
        for f in ['can_access_dashboard','can_access_assets','can_access_workrequest',
                  'can_access_workorder','can_access_pm','can_access_reports',
                  'can_create_wr','can_convert_wr','can_create_wo','can_close_wo',
                  'can_manage_assets','can_manage_pm',
                  'can_access_safety','can_approve_safety',
                  'notify_wr_new','notify_wr_converted','notify_wr_rejected',
                  'notify_wo_assigned','notify_wo_completed','notify_wo_overdue',
                  'notify_pm_due','notify_pm_overdue','notify_safety_permit']:
            setattr(self, f, False)

        self.can_access_dashboard = True  # everyone sees dashboard

        if role == 'admin':
            for f in ['can_access_assets','can_access_workrequest','can_access_workorder',
                      'can_access_pm','can_access_reports','can_create_wr','can_convert_wr',
                      'can_create_wo','can_close_wo','can_manage_assets','can_manage_pm',
                      'can_access_safety','can_approve_safety',
                      'notify_wr_new','notify_wr_converted','notify_wr_rejected',
                      'notify_wo_assigned','notify_wo_completed','notify_wo_overdue',
                      'notify_pm_due','notify_pm_overdue','notify_safety_permit']:
                setattr(self, f, True)

        elif role == 'section_head':
            for f in ['can_access_assets','can_access_workrequest','can_access_workorder',
                      'can_access_pm','can_access_reports','can_create_wr','can_convert_wr',
                      'can_create_wo','can_close_wo','can_manage_assets','can_manage_pm',
                      'can_access_safety','can_approve_safety',
                      'notify_wr_new','notify_wr_converted','notify_wr_rejected',
                      'notify_wo_assigned','notify_wo_completed','notify_wo_overdue',
                      'notify_pm_due','notify_pm_overdue','notify_safety_permit']:
                setattr(self, f, True)

        elif role == 'engineer':
            for f in ['can_access_assets','can_access_workrequest','can_access_workorder',
                      'can_access_pm','can_access_reports','can_create_wr','can_create_wo',
                      'can_close_wo','can_manage_pm','can_access_safety',
                      'notify_wr_new','notify_wo_assigned','notify_wo_overdue',
                      'notify_pm_due','notify_pm_overdue','notify_safety_permit']:
                setattr(self, f, True)

        elif role == 'technician':
            for f in ['can_access_workrequest','can_access_workorder','can_access_safety',
                      'can_create_wr','notify_wo_assigned']:
                setattr(self, f, True)

        elif role == 'operator':
            self.can_access_workrequest = True
            self.can_create_wr = True
            self.notify_wr_converted = True
            self.notify_wo_completed = True

        elif role == 'viewer':
            for f in ['can_access_assets','can_access_workrequest','can_access_workorder',
                      'can_access_pm','can_access_reports','can_access_safety']:
                setattr(self, f, True)

    class Meta:
        ordering = ['user__username']


class Notification(models.Model):
    TYPE_CHOICES = [
        ('wr_new',       'New Work Request'),
        ('wr_converted', 'Work Request Converted to WO'),
        ('wo_assigned',  'Work Order Assigned'),
        ('wo_completed', 'Work Order Completed'),
        ('wo_overdue',   'Work Order Overdue'),
        ('pm_due',       'PM Task Due'),
        ('pm_overdue',   'PM Task Overdue'),
        ('wr_rejected',  'Work Request Rejected'),
    ]
    PRIORITY_CHOICES = [
        ('critical', 'Critical'),
        ('high',     'High'),
        ('normal',   'Normal'),
        ('low',      'Low'),
    ]

    recipient     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notif_type    = models.CharField(max_length=30, choices=TYPE_CHOICES)
    priority      = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    title         = models.CharField(max_length=200)
    message       = models.TextField()
    link          = models.CharField(max_length=300, blank=True)  # URL to redirect on click
    is_read       = models.BooleanField(default=False)
    created_at    = models.DateTimeField(auto_now_add=True)

    # Optional references
    work_request  = models.ForeignKey('WorkRequest', on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    work_order    = models.ForeignKey('WorkOrder',   on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')

    def __str__(self):
        return f"→ {self.recipient.username}: {self.title}"

    class Meta:
        ordering = ['-created_at']


class CompanySettings(models.Model):
    """
    Singleton model — only ONE record exists.
    Admin fills this in; all users see it in the header bar.
    """
    factory_name     = models.CharField(max_length=200, default='My Factory', verbose_name='Factory / Company Name')
    factory_name_ar  = models.CharField(max_length=200, blank=True, verbose_name='Factory Name (Arabic)')
    location         = models.CharField(max_length=300, blank=True, verbose_name='Location / Address')
    location_ar      = models.CharField(max_length=300, blank=True, verbose_name='Location (Arabic)')
    logo_text        = models.CharField(max_length=10, blank=True, default='🏭', verbose_name='Logo Icon/Emoji')
    phone            = models.CharField(max_length=50, blank=True, verbose_name='Contact Phone')
    email            = models.EmailField(blank=True, verbose_name='Contact Email')
    website          = models.CharField(max_length=200, blank=True, verbose_name='Website')
    welcome_message  = models.CharField(max_length=300, blank=True, verbose_name='Welcome Message (English)')
    welcome_message_ar = models.CharField(max_length=300, blank=True, verbose_name='Welcome Message (Arabic)')
    updated_by       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    updated_at       = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Company Settings — {self.factory_name}"

    def save(self, *args, **kwargs):
        # Enforce singleton — only one record allowed
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={'factory_name': 'My Factory'})
        return obj

    class Meta:
        verbose_name = 'Company Settings'
        verbose_name_plural = 'Company Settings'


# ── PREDICTIVE MAINTENANCE ─────────────────────────────────────────────────

class PredictiveRecord(models.Model):
    """Log sensor readings and condition monitoring data for assets."""
    CONDITION_CHOICES = [
        ('Good',     'Good'),
        ('Warning',  'Warning'),
        ('Critical', 'Critical'),
        ('Failed',   'Failed'),
    ]
    PARAMETER_CHOICES = [
        ('Temperature',  'Temperature (°C)'),
        ('Vibration',    'Vibration (mm/s)'),
        ('Current',      'Current (A)'),
        ('Voltage',      'Voltage (V)'),
        ('Pressure',     'Pressure (bar)'),
        ('RPM',          'Speed (RPM)'),
        ('Oil Level',    'Oil Level (%)'),
        ('Noise',        'Noise Level (dB)'),
        ('Humidity',     'Humidity (%)'),
        ('Power',        'Power (kW)'),
        ('Other',        'Other'),
    ]

    asset         = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='predictive_records')
    parameter     = models.CharField(max_length=50, choices=PARAMETER_CHOICES)
    value         = models.DecimalField(max_digits=10, decimal_places=2)
    unit          = models.CharField(max_length=20, blank=True)
    normal_min    = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    normal_max    = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    condition     = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='Good')
    notes         = models.TextField(blank=True)
    recorded_by   = models.CharField(max_length=100, blank=True)
    recorded_at   = models.DateTimeField(default=timezone.now)
    created_at    = models.DateTimeField(auto_now_add=True)

    def calculate_condition(self):
        if self.normal_min is not None and self.normal_max is not None:
            val = float(self.value)
            mn  = float(self.normal_min)
            mx  = float(self.normal_max)
            rng = mx - mn
            if val < mn or val > mx:
                deviation = min(abs(val - mn), abs(val - mx))
                if deviation > rng * 0.3:
                    return 'Critical'
                return 'Warning'
            return 'Good'
        return self.condition

    def __str__(self):
        return f"{self.asset.name} — {self.parameter}: {self.value}"

    class Meta:
        ordering = ['-recorded_at']


# ── PROACTIVE MAINTENANCE ──────────────────────────────────────────────────

class ProactiveAction(models.Model):
    """Planned proactive actions based on inspection findings or trends."""
    PRIORITY_CHOICES = [
        ('Critical', 'Critical'),
        ('High',     'High'),
        ('Medium',   'Medium'),
        ('Low',      'Low'),
    ]
    STATUS_CHOICES = [
        ('Planned',     'Planned'),
        ('In Progress', 'In Progress'),
        ('Completed',   'Completed'),
        ('Cancelled',   'Cancelled'),
    ]
    TYPE_CHOICES = [
        ('Lubrication',        'Lubrication'),
        ('Alignment',          'Alignment'),
        ('Belt Replacement',   'Belt Replacement'),
        ('Filter Change',      'Filter Change'),
        ('Calibration',        'Calibration'),
        ('Cleaning',           'Cleaning'),
        ('Tightening',         'Tightening'),
        ('Adjustment',         'Adjustment'),
        ('Part Replacement',   'Part Replacement'),
        ('Inspection',         'Inspection'),
        ('Other',              'Other'),
    ]

    asset         = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='proactive_actions')
    title         = models.CharField(max_length=200)
    action_type   = models.CharField(max_length=50, choices=TYPE_CHOICES)
    priority      = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Medium')
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Planned')
    trigger_reason = models.TextField(help_text='What observation or data triggered this action?')
    action_plan   = models.TextField(blank=True, help_text='Detailed steps to take')
    assigned_to   = models.CharField(max_length=100, blank=True)
    planned_date  = models.DateField()
    completed_date = models.DateField(null=True, blank=True)
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    actual_hours  = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    result        = models.TextField(blank=True, help_text='Outcome after action was taken')
    created_by    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    def is_overdue(self):
        from datetime import date
        return self.planned_date < date.today() and self.status not in ['Completed', 'Cancelled']

    def __str__(self):
        return f"{self.title} — {self.asset.name}"

    class Meta:
        ordering = ['planned_date']


# ── BREAKDOWN ANALYSIS ─────────────────────────────────────────────────────

class BreakdownAnalysis(models.Model):
    """Root cause analysis and failure analysis for completed breakdowns."""
    CAUSE_CATEGORY = [
        ('Mechanical',   'Mechanical Failure'),
        ('Electrical',   'Electrical Failure'),
        ('Operational',  'Operational Error'),
        ('Design',       'Design Deficiency'),
        ('Maintenance',  'Maintenance Error'),
        ('External',     'External Factor'),
        ('Wear',         'Normal Wear & Tear'),
        ('Unknown',      'Unknown'),
    ]
    METHOD_CHOICES = [
        ('5-Why',        '5-Why Analysis'),
        ('Fishbone',     'Fishbone (Ishikawa)'),
        ('FMEA',         'FMEA'),
        ('RCA',          'Root Cause Analysis'),
        ('Other',        'Other'),
    ]

    work_order      = models.OneToOneField(WorkOrder, on_delete=models.CASCADE,
                                           related_name='breakdown_analysis', null=True, blank=True)
    work_request    = models.ForeignKey(WorkRequest, on_delete=models.SET_NULL,
                                         null=True, blank=True, related_name='analyses')
    asset           = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='breakdown_analyses')
    title           = models.CharField(max_length=200)
    failure_date    = models.DateField()
    restored_date   = models.DateField(null=True, blank=True)
    total_downtime  = models.DecimalField(max_digits=8, decimal_places=1, null=True, blank=True,
                                          help_text='Total downtime in hours')
    production_loss = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                          help_text='Estimated production loss (EGP)')
    repair_cost     = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cause_category  = models.CharField(max_length=30, choices=CAUSE_CATEGORY)
    analysis_method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='5-Why')

    # 5-Why fields
    why_1 = models.TextField(blank=True, verbose_name='Why 1 — What failed?')
    why_2 = models.TextField(blank=True, verbose_name='Why 2 — Why did it fail?')
    why_3 = models.TextField(blank=True, verbose_name='Why 3 — Why did that happen?')
    why_4 = models.TextField(blank=True, verbose_name='Why 4 — Why was that the case?')
    why_5 = models.TextField(blank=True, verbose_name='Why 5 — Root Cause')

    root_cause          = models.TextField(help_text='Final determined root cause')
    corrective_actions  = models.TextField(help_text='What was done to fix this breakdown?')
    preventive_actions  = models.TextField(blank=True, help_text='What will prevent this from happening again?')
    lessons_learned     = models.TextField(blank=True)
    recurrence_risk     = models.CharField(max_length=10, choices=[
        ('High','High'),('Medium','Medium'),('Low','Low')], default='Medium')
    analysed_by         = models.CharField(max_length=100, blank=True)
    approved_by         = models.CharField(max_length=100, blank=True)
    created_at          = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"BDA — {self.asset.name} ({self.failure_date})"

    class Meta:
        ordering = ['-failure_date']
        verbose_name = 'Breakdown Analysis'
        verbose_name_plural = 'Breakdown Analyses'


# ── FACILITIES MANAGEMENT ──────────────────────────────────────────────────

class Facility(models.Model):
    """Locations, buildings, floors and zones in the facility."""
    TYPE_CHOICES = [
        ('Building',      'Building'),
        ('Floor',         'Floor'),
        ('Hall',          'Production Hall'),
        ('Zone',          'Zone / Area'),
        ('Substation',    'Electrical Substation'),
        ('Utility Room',  'Utility Room'),
        ('Warehouse',     'Warehouse'),
        ('Office',        'Office'),
        ('Outdoor',       'Outdoor Area'),
        ('Other',         'Other'),
    ]
    STATUS_CHOICES = [
        ('Active',        'Active / In Use'),
        ('Under Renovation', 'Under Renovation'),
        ('Closed',        'Closed'),
    ]

    code          = models.CharField(max_length=20, unique=True)
    name          = models.CharField(max_length=200)
    name_ar       = models.CharField(max_length=200, blank=True)
    facility_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    parent        = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='sub_facilities')
    status        = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Active')
    area_sqm      = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                        help_text='Area in square meters')
    responsible_person = models.CharField(max_length=100, blank=True)
    phone         = models.CharField(max_length=30, blank=True)
    notes         = models.TextField(blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    def asset_count(self):
        return Asset.objects.filter(location__icontains=self.name).count()

    def __str__(self):
        return f"{self.code} — {self.name}"

    class Meta:
        ordering = ['code']
        verbose_name_plural = 'Facilities'


class FacilityServiceRequest(models.Model):
    """Service requests for facility issues — cleaning, AC, plumbing, civil works."""
    CATEGORY_CHOICES = [
        ('Civil',         'Civil / Construction'),
        ('Electrical',    'Electrical'),
        ('Plumbing',      'Plumbing'),
        ('HVAC',          'HVAC / Air Conditioning'),
        ('Cleaning',      'Cleaning / Housekeeping'),
        ('Security',      'Security'),
        ('IT',            'IT / Network'),
        ('Fire Safety',   'Fire Safety'),
        ('Pest Control',  'Pest Control'),
        ('Other',         'Other'),
    ]
    PRIORITY_CHOICES = [
        ('Urgent',   'Urgent'),
        ('High',     'High'),
        ('Medium',   'Medium'),
        ('Low',      'Low'),
    ]
    STATUS_CHOICES = [
        ('Open',        'Open'),
        ('In Progress', 'In Progress'),
        ('Completed',   'Completed'),
        ('Rejected',    'Rejected'),
    ]

    sr_number     = models.CharField(max_length=20, unique=True, editable=False)
    facility      = models.ForeignKey(Facility, on_delete=models.SET_NULL, null=True,
                                      related_name='service_requests')
    category      = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    priority      = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Medium')
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    title         = models.CharField(max_length=200)
    description   = models.TextField()
    reported_by   = models.CharField(max_length=100)
    reporter_phone = models.CharField(max_length=30, blank=True)
    assigned_to   = models.CharField(max_length=100, blank=True)
    due_date      = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    cost          = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes         = models.TextField(blank=True)
    created_by    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.sr_number:
            last = FacilityServiceRequest.objects.order_by('id').last()
            num  = (last.id + 1) if last else 1
            self.sr_number = f"SR-{num:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.sr_number} — {self.title}"

    class Meta:
        ordering = ['-created_at']


# ══════════════════════════════════════════════════════════════════════════
# ISO MODULES
# ══════════════════════════════════════════════════════════════════════════

# ── MODULE 1: CALIBRATION MANAGEMENT ──────────────────────────────────────

class Instrument(models.Model):
    """Measuring instruments and gauges requiring calibration."""
    TYPE_CHOICES = [
        ('Pressure Gauge',    'Pressure Gauge'),
        ('Temperature',       'Temperature Meter/Sensor'),
        ('Multimeter',        'Electrical Multimeter'),
        ('Clamp Meter',       'Clamp Meter'),
        ('Torque Wrench',     'Torque Wrench'),
        ('Vernier Caliper',   'Vernier Caliper'),
        ('Micrometer',        'Micrometer'),
        ('Flow Meter',        'Flow Meter'),
        ('Vibration Meter',   'Vibration Meter'),
        ('Sound Level Meter', 'Sound Level Meter'),
        ('Scale/Balance',     'Scale / Balance'),
        ('Thermometer',       'Thermometer'),
        ('Hygrometer',        'Hygrometer'),
        ('Tachometer',        'Tachometer'),
        ('Power Analyzer',    'Power Analyzer'),
        ('Other',             'Other'),
    ]
    FREQUENCY_CHOICES = [
        ('Monthly',    'Monthly'),
        ('Quarterly',  'Quarterly (3 months)'),
        ('Semi-Annual','Semi-Annual (6 months)'),
        ('Annual',     'Annual (12 months)'),
        ('2 Years',    'Every 2 Years'),
    ]
    STATUS_CHOICES = [
        ('Active',      'Active — In Service'),
        ('Due',         'Calibration Due'),
        ('Overdue',     'Overdue'),
        ('In Cal',      'Sent for Calibration'),
        ('Out of Service', 'Out of Service'),
        ('Scrapped',    'Scrapped'),
    ]

    instrument_id    = models.CharField(max_length=50, unique=True)
    name             = models.CharField(max_length=200)
    instrument_type  = models.CharField(max_length=50, choices=TYPE_CHOICES)
    manufacturer     = models.CharField(max_length=100, blank=True)
    model_number     = models.CharField(max_length=100, blank=True)
    serial_number    = models.CharField(max_length=100, blank=True)
    range_min        = models.CharField(max_length=50, blank=True, verbose_name='Measurement Range Min')
    range_max        = models.CharField(max_length=50, blank=True, verbose_name='Measurement Range Max')
    unit             = models.CharField(max_length=30, blank=True, verbose_name='Measurement Unit')
    accuracy         = models.CharField(max_length=50, blank=True, verbose_name='Accuracy / Tolerance')
    location         = models.CharField(max_length=200, blank=True)
    asset            = models.ForeignKey(Asset, on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='instruments', verbose_name='Used on Asset')
    responsible_person = models.CharField(max_length=100, blank=True)
    calibration_frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='Annual')
    last_calibration = models.DateField(null=True, blank=True)
    next_calibration = models.DateField(null=True, blank=True)
    calibration_lab  = models.CharField(max_length=200, blank=True, verbose_name='Calibration Laboratory')
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    iso_reference    = models.CharField(max_length=100, blank=True, default='ISO 9001:2015 Cl.7.1.5',
                                        verbose_name='ISO Reference')
    notes            = models.TextField(blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    def is_overdue(self):
        from datetime import date
        return self.next_calibration and self.next_calibration < date.today()

    def days_until_due(self):
        from datetime import date
        if self.next_calibration:
            return (self.next_calibration - date.today()).days
        return None

    def __str__(self):
        return f"{self.instrument_id} — {self.name}"

    class Meta:
        ordering = ['next_calibration']


class CalibrationRecord(models.Model):
    """History of calibration events for each instrument."""
    RESULT_CHOICES = [
        ('Pass',           'Pass — Within Tolerance'),
        ('Pass with Note', 'Pass with Note'),
        ('Fail',           'Fail — Out of Tolerance'),
        ('Adjusted',       'Adjusted & Pass'),
        ('Scrapped',       'Scrapped'),
    ]

    instrument       = models.ForeignKey(Instrument, on_delete=models.CASCADE,
                                          related_name='calibration_records')
    calibration_date = models.DateField()
    next_due         = models.DateField()
    performed_by     = models.CharField(max_length=100)
    lab_name         = models.CharField(max_length=200, blank=True)
    certificate_number = models.CharField(max_length=100, blank=True)
    result           = models.CharField(max_length=20, choices=RESULT_CHOICES)
    reading_before   = models.CharField(max_length=100, blank=True, verbose_name='Reading Before Calibration')
    reading_after    = models.CharField(max_length=100, blank=True, verbose_name='Reading After Calibration')
    reference_standard = models.CharField(max_length=200, blank=True)
    temperature_c    = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True,
                                           verbose_name='Ambient Temperature (°C)')
    humidity_pct     = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True,
                                           verbose_name='Humidity (%)')
    notes            = models.TextField(blank=True)
    created_by       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.instrument.instrument_id} — {self.calibration_date} — {self.result}"

    class Meta:
        ordering = ['-calibration_date']


# ── MODULE 2: NCR & CORRECTIVE ACTIONS ────────────────────────────────────

class NonConformance(models.Model):
    """Non-Conformance Reports (NCR) — ISO 9001 Cl.10.2, ISO 14001 Cl.10.2"""
    SOURCE_CHOICES = [
        ('Internal Audit',    'Internal Audit'),
        ('External Audit',    'External Audit (Certification Body)'),
        ('Customer Complaint','Customer Complaint'),
        ('Process Monitoring','Process Monitoring'),
        ('Supplier Issue',    'Supplier Issue'),
        ('Incident',          'Incident / Near Miss'),
        ('Inspection',        'Inspection Finding'),
        ('Other',             'Other'),
    ]
    GRADE_CHOICES = [
        ('Major',       'Major Non-Conformance'),
        ('Minor',       'Minor Non-Conformance'),
        ('Observation', 'Observation'),
        ('Opportunity', 'Opportunity for Improvement'),
    ]
    ISO_CHOICES = [
        ('ISO 9001',  'ISO 9001:2015'),
        ('ISO 14001', 'ISO 14001:2015'),
        ('ISO 55001', 'ISO 55001:2014'),
        ('ISO 45001', 'ISO 45001:2018'),
        ('Internal',  'Internal Standard'),
        ('Other',     'Other'),
    ]
    STATUS_CHOICES = [
        ('Open',           'Open'),
        ('Under Analysis', 'Under Root Cause Analysis'),
        ('Action Planned', 'Corrective Action Planned'),
        ('In Progress',    'Corrective Action In Progress'),
        ('Completed',      'Action Completed'),
        ('Verified',       'Verified Effective — Closed'),
        ('Rejected',       'Rejected / Invalid'),
    ]

    ncr_number       = models.CharField(max_length=20, unique=True, editable=False)
    title            = models.CharField(max_length=200)
    source           = models.CharField(max_length=30, choices=SOURCE_CHOICES)
    grade            = models.CharField(max_length=20, choices=GRADE_CHOICES)
    iso_standard     = models.CharField(max_length=20, choices=ISO_CHOICES)
    iso_clause       = models.CharField(max_length=50, blank=True,
                                        verbose_name='ISO Clause Reference',
                                        help_text='e.g. 7.1.5, 8.1, 10.2')
    department       = models.CharField(max_length=100, blank=True)
    description      = models.TextField(verbose_name='Description of Non-Conformance')
    evidence         = models.TextField(blank=True, verbose_name='Objective Evidence')
    immediate_action = models.TextField(blank=True, verbose_name='Immediate / Containment Action')
    root_cause       = models.TextField(blank=True)
    corrective_action = models.TextField(blank=True)
    preventive_action = models.TextField(blank=True)
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    raised_by        = models.CharField(max_length=100)
    assigned_to      = models.CharField(max_length=100, blank=True)
    target_date      = models.DateField(null=True, blank=True)
    completed_date   = models.DateField(null=True, blank=True)
    verified_by      = models.CharField(max_length=100, blank=True)
    verified_date    = models.DateField(null=True, blank=True)
    verification_notes = models.TextField(blank=True)
    linked_wo        = models.ForeignKey(WorkOrder, on_delete=models.SET_NULL,
                                          null=True, blank=True, related_name='ncrs')
    created_by       = models.ForeignKey(User, on_delete=models.SET_NULL,
                                          null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.ncr_number:
            last = NonConformance.objects.order_by('id').last()
            num  = (last.id + 1) if last else 1
            self.ncr_number = f"NCR-{num:04d}"
        super().save(*args, **kwargs)

    def is_overdue(self):
        from datetime import date
        return (self.target_date and self.target_date < date.today()
                and self.status not in ['Verified', 'Rejected'])

    def __str__(self):
        return f"{self.ncr_number} — {self.title}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Non-Conformance'
        verbose_name_plural = 'Non-Conformances'


# ── MODULE 3: ISO DOCUMENT CONTROL ────────────────────────────────────────

class ISODocument(models.Model):
    """Controlled documents — procedures, work instructions, forms, records."""
    TYPE_CHOICES = [
        ('Procedure',         'Procedure (PR)'),
        ('Work Instruction',  'Work Instruction (WI)'),
        ('Form',              'Form / Template (FM)'),
        ('Record',            'Record (RC)'),
        ('Policy',            'Policy'),
        ('Manual',            'Manual'),
        ('External Document', 'External Document'),
        ('Drawing',           'Drawing / Specification'),
    ]
    STATUS_CHOICES = [
        ('Draft',    'Draft'),
        ('Review',   'Under Review'),
        ('Approved', 'Approved — Controlled'),
        ('Obsolete', 'Obsolete'),
    ]
    ISO_CHOICES = [
        ('ISO 9001',  'ISO 9001:2015'),
        ('ISO 14001', 'ISO 14001:2015'),
        ('ISO 55001', 'ISO 55001:2014'),
        ('All',       'All Standards'),
        ('Internal',  'Internal Only'),
    ]

    doc_number       = models.CharField(max_length=50, unique=True, verbose_name='Document Number')
    title            = models.CharField(max_length=300)
    doc_type         = models.CharField(max_length=30, choices=TYPE_CHOICES)
    iso_standard     = models.CharField(max_length=20, choices=ISO_CHOICES)
    iso_clause       = models.CharField(max_length=100, blank=True, verbose_name='Related ISO Clause(s)')
    department       = models.CharField(max_length=100, blank=True)
    revision         = models.CharField(max_length=10, default='00', verbose_name='Revision No.')
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    prepared_by      = models.CharField(max_length=100, blank=True)
    reviewed_by      = models.CharField(max_length=100, blank=True)
    approved_by      = models.CharField(max_length=100, blank=True)
    issue_date       = models.DateField(null=True, blank=True)
    review_date      = models.DateField(null=True, blank=True, verbose_name='Next Review Date')
    scope            = models.TextField(blank=True, verbose_name='Scope / Purpose')
    location         = models.CharField(max_length=300, blank=True,
                                        verbose_name='Storage Location / File Path',
                                        help_text='e.g. Server/ISO/Procedures/PR-001 or SharePoint link')
    change_summary   = models.TextField(blank=True, verbose_name='Change / Revision Summary')
    notes            = models.TextField(blank=True)
    created_by       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    def is_due_for_review(self):
        from datetime import date
        return self.review_date and self.review_date <= date.today()

    def __str__(self):
        return f"{self.doc_number} Rev.{self.revision} — {self.title}"

    class Meta:
        ordering = ['doc_number']
        verbose_name = 'ISO Document'


# ── MODULE 4: INTERNAL AUDIT ───────────────────────────────────────────────

class InternalAudit(models.Model):
    """Internal audit plans and results."""
    TYPE_CHOICES = [
        ('System',   'System Audit'),
        ('Process',  'Process Audit'),
        ('Product',  'Product / Output Audit'),
        ('Supplier', 'Supplier Audit'),
    ]
    STATUS_CHOICES = [
        ('Planned',    'Planned'),
        ('In Progress','In Progress'),
        ('Completed',  'Completed'),
        ('Cancelled',  'Cancelled'),
    ]
    ISO_CHOICES = [
        ('ISO 9001',  'ISO 9001:2015'),
        ('ISO 14001', 'ISO 14001:2015'),
        ('ISO 55001', 'ISO 55001:2014'),
        ('Combined',  'Combined Audit'),
    ]

    audit_number     = models.CharField(max_length=20, unique=True, editable=False)
    title            = models.CharField(max_length=200)
    iso_standard     = models.CharField(max_length=20, choices=ISO_CHOICES)
    audit_type       = models.CharField(max_length=20, choices=TYPE_CHOICES, default='System')
    department       = models.CharField(max_length=100)
    clauses_audited  = models.CharField(max_length=300, blank=True,
                                         help_text='e.g. 4.1, 4.2, 7.1, 8.1')
    lead_auditor     = models.CharField(max_length=100)
    audit_team       = models.TextField(blank=True, help_text='Other auditors involved')
    auditee          = models.CharField(max_length=100, blank=True, verbose_name='Auditee / Department Head')
    planned_date     = models.DateField()
    actual_date      = models.DateField(null=True, blank=True)
    duration_hours   = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Planned')
    scope            = models.TextField(blank=True)
    checklist_notes  = models.TextField(blank=True, verbose_name='Audit Checklist & Notes')
    summary          = models.TextField(blank=True, verbose_name='Audit Summary')
    major_nc_count   = models.PositiveIntegerField(default=0, verbose_name='Major NCs Found')
    minor_nc_count   = models.PositiveIntegerField(default=0, verbose_name='Minor NCs Found')
    observation_count = models.PositiveIntegerField(default=0, verbose_name='Observations')
    ofi_count        = models.PositiveIntegerField(default=0, verbose_name='Opportunities for Improvement')
    overall_result   = models.CharField(max_length=50, blank=True,
                                         verbose_name='Overall Audit Result')
    next_audit_date  = models.DateField(null=True, blank=True)
    created_by       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.audit_number:
            last = InternalAudit.objects.order_by('id').last()
            num  = (last.id + 1) if last else 1
            self.audit_number = f"AUD-{num:04d}"
        super().save(*args, **kwargs)

    def total_findings(self):
        return self.major_nc_count + self.minor_nc_count + self.observation_count + self.ofi_count

    def __str__(self):
        return f"{self.audit_number} — {self.title}"

    class Meta:
        ordering = ['-planned_date']


# ── MODULE 5: ENVIRONMENTAL ASPECTS (ISO 14001) ────────────────────────────

class EnvironmentalAspect(models.Model):
    """Environmental aspects and impacts register — ISO 14001 Cl.6.1.2"""
    ASPECT_CHOICES = [
        ('Air Emission',      'Air Emission'),
        ('Water Discharge',   'Water Discharge'),
        ('Waste Generation',  'Waste Generation'),
        ('Soil Contamination','Soil Contamination'),
        ('Energy Use',        'Energy Use'),
        ('Water Use',         'Water Consumption'),
        ('Noise',             'Noise / Vibration'),
        ('Chemical Use',      'Chemical Use / Storage'),
        ('Spill Risk',        'Spill / Leak Risk'),
        ('Other',             'Other'),
    ]
    CONDITION_CHOICES = [
        ('Normal',     'Normal Operations'),
        ('Abnormal',   'Abnormal Operations'),
        ('Emergency',  'Emergency Conditions'),
    ]
    SIGNIFICANCE_CHOICES = [
        ('Significant',     'Significant'),
        ('Non-Significant', 'Non-Significant'),
    ]

    aspect_number    = models.CharField(max_length=20, unique=True, editable=False)
    activity         = models.CharField(max_length=200, verbose_name='Activity / Process / Product')
    aspect           = models.CharField(max_length=50, choices=ASPECT_CHOICES)
    impact           = models.CharField(max_length=300, verbose_name='Environmental Impact')
    condition        = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='Normal')
    department       = models.CharField(max_length=100, blank=True)
    asset            = models.ForeignKey(Asset, on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name='env_aspects')
    # Significance evaluation (1-5 scale)
    severity         = models.IntegerField(default=3, verbose_name='Severity (1-5)')
    probability      = models.IntegerField(default=3, verbose_name='Probability (1-5)')
    detection        = models.IntegerField(default=3, verbose_name='Detection Difficulty (1-5)')
    significance_score = models.IntegerField(default=0, editable=False)
    significance     = models.CharField(max_length=20, choices=SIGNIFICANCE_CHOICES,
                                         default='Non-Significant')
    legal_requirement = models.TextField(blank=True, verbose_name='Applicable Legal Requirements')
    control_measure  = models.TextField(blank=True, verbose_name='Control Measures / Actions')
    objective        = models.TextField(blank=True, verbose_name='Environmental Objective / Target')
    responsible      = models.CharField(max_length=100, blank=True)
    review_date      = models.DateField(null=True, blank=True)
    notes            = models.TextField(blank=True)
    created_by       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.aspect_number:
            last = EnvironmentalAspect.objects.order_by('id').last()
            num  = (last.id + 1) if last else 1
            self.aspect_number = f"ENV-{num:04d}"
        self.significance_score = self.severity * self.probability * self.detection
        self.significance = 'Significant' if self.significance_score >= 27 else 'Non-Significant'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.aspect_number} — {self.activity} / {self.aspect}"

    class Meta:
        ordering = ['-significance_score']


# ── SAFETY PERMIT MODULE (Work Permit / Permit to Work) ───────────────────

class SafetyPermit(models.Model):
    """
    Digital Permit to Work — replaces paper safety permission forms.
    Automatically generated when a Work Order is created, reviewed and
    approved by a safety-authorized user before maintenance work starts.
    """
    PERMIT_TYPE_CHOICES = [
        ('General',         'General Work Permit'),
        ('Hot Work',        'Hot Work Permit (Welding/Cutting/Grinding)'),
        ('Confined Space',  'Confined Space Entry Permit'),
        ('Electrical',      'Electrical Isolation / LOTO Permit'),
        ('Working at Height','Working at Height Permit'),
        ('Excavation',      'Excavation Permit'),
        ('Lifting',         'Lifting Operation Permit'),
        ('Chemical',        'Chemical Handling Permit'),
        ('Other',           'Other'),
    ]
    STATUS_CHOICES = [
        ('Pending',   'Pending Approval'),
        ('Approved',  'Approved — Work May Start'),
        ('Active',    'Active — Work In Progress'),
        ('Suspended', 'Suspended'),
        ('Closed',    'Closed — Work Completed'),
        ('Rejected',  'Rejected'),
        ('Expired',   'Expired'),
    ]
    RISK_LEVEL_CHOICES = [
        ('Low',      'Low Risk'),
        ('Medium',   'Medium Risk'),
        ('High',     'High Risk'),
        ('Critical', 'Critical Risk'),
    ]

    permit_number     = models.CharField(max_length=20, unique=True, editable=False)
    work_order        = models.ForeignKey(WorkOrder, on_delete=models.CASCADE,
                                          related_name='safety_permits')
    permit_type       = models.CharField(max_length=30, choices=PERMIT_TYPE_CHOICES, default='General')
    status            = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    risk_level        = models.CharField(max_length=20, choices=RISK_LEVEL_CHOICES, default='Medium')

    # Work details — pulled from WO automatically, editable
    work_description  = models.TextField(verbose_name='Description of Work to be Performed')
    location          = models.CharField(max_length=300, blank=True)

    # People
    requested_by      = models.CharField(max_length=100, verbose_name='Permit Requested By (Technician)')
    workers_involved   = models.TextField(blank=True, verbose_name='Names of All Workers on Site')
    supervisor         = models.CharField(max_length=100, blank=True, verbose_name='Direct Supervisor')
    approved_by        = models.CharField(max_length=100, blank=True, verbose_name='Safety Officer / Approver')

    # Hazards & precautions (checklist style, stored as text for flexibility)
    hazards_identified  = models.TextField(blank=True, verbose_name='Hazards Identified')
    ppe_required        = models.TextField(blank=True, verbose_name='Required PPE')
    precautions_taken   = models.TextField(blank=True, verbose_name='Precautions / Control Measures')
    isolation_required  = models.BooleanField(default=False, verbose_name='Isolation / LOTO Required')
    isolation_details    = models.TextField(blank=True, verbose_name='Isolation Details (points, tags, locks)')
    fire_watch_required  = models.BooleanField(default=False, verbose_name='Fire Watch Required')
    gas_test_required    = models.BooleanField(default=False, verbose_name='Gas Test Required')
    gas_test_result      = models.CharField(max_length=200, blank=True, verbose_name='Gas Test Result')

    # Validity
    valid_from         = models.DateTimeField(default=timezone.now)
    valid_until         = models.DateTimeField(null=True, blank=True)

    # Approval trail
    approval_notes      = models.TextField(blank=True)
    rejection_reason     = models.TextField(blank=True)
    approved_at          = models.DateTimeField(null=True, blank=True)

    # Closure
    closed_by           = models.CharField(max_length=100, blank=True)
    closed_at            = models.DateTimeField(null=True, blank=True)
    closure_notes        = models.TextField(blank=True, verbose_name='Site Cleared / Closure Notes')

    created_by          = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                            related_name='created_permits')
    created_at           = models.DateTimeField(auto_now_add=True)
    updated_at            = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.permit_number:
            last = SafetyPermit.objects.order_by('id').last()
            num  = (last.id + 1) if last else 1
            self.permit_number = f"PTW-{num:04d}"
        super().save(*args, **kwargs)

    def is_expired(self):
        from datetime import datetime
        return (self.valid_until and self.valid_until < timezone.now()
                and self.status not in ['Closed', 'Rejected'])

    def response_time_hours(self):
        """
        Time from permit creation (requested) to the safety officer's
        decision (approved_at — set on both Approve and Reject).
        Returns None if not yet decided.
        """
        if self.approved_at and self.created_at:
            delta = self.approved_at - self.created_at
            return round(delta.total_seconds() / 3600, 2)
        return None

    def response_time_display(self):
        """Human-friendly response time, e.g. '2h 15m' or '1d 3h'."""
        hours = self.response_time_hours()
        if hours is None:
            return None
        total_minutes = int(hours * 60)
        days, rem_minutes = divmod(total_minutes, 1440)
        hrs, mins = divmod(rem_minutes, 60)
        if days > 0:
            return f"{days}d {hrs}h"
        elif hrs > 0:
            return f"{hrs}h {mins}m"
        else:
            return f"{mins}m"

    def __str__(self):
        return f"{self.permit_number} — {self.get_permit_type_display()} — {self.work_order.wo_number}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Safety Permit'
        verbose_name_plural = 'Safety Permits'
