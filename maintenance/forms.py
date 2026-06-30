from django import forms
from .models import (Asset, WorkOrder, PMSchedule, SparePartUsage, WorkRequest,
                     CompanySettings, PredictiveRecord, ProactiveAction,
                     BreakdownAnalysis, Facility, FacilityServiceRequest)


class CompanySettingsForm(forms.ModelForm):
    class Meta:
        model = CompanySettings
        fields = [
            'factory_name', 'factory_name_ar', 'location', 'location_ar',
            'logo_text', 'phone', 'email', 'website',
            'welcome_message', 'welcome_message_ar',
        ]
        widgets = {
            'welcome_message':    forms.TextInput(attrs={'placeholder': 'e.g. Welcome to our maintenance system'}),
            'welcome_message_ar': forms.TextInput(attrs={'placeholder': 'مثال: مرحباً بكم في نظام الصيانة', 'dir': 'rtl'}),
            'factory_name_ar':    forms.TextInput(attrs={'dir': 'rtl'}),
            'location_ar':        forms.TextInput(attrs={'dir': 'rtl'}),
        }


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = [
            'asset_id', 'name', 'category', 'location', 'status',
            'manufacturer', 'model_number', 'serial_number',
            'purchase_date', 'last_pm_date', 'notes'
        ]
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
            'last_pm_date':  forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class WorkOrderForm(forms.ModelForm):
    class Meta:
        model = WorkOrder
        fields = [
            'title', 'asset', 'wo_type', 'priority', 'status',
            'assigned_to', 'due_date', 'estimated_hours', 'actual_hours',
            'labor_cost', 'description', 'notes'
        ]
        widgets = {
            'due_date':    forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'notes':       forms.Textarea(attrs={'rows': 2}),
        }


class PMScheduleForm(forms.ModelForm):
    class Meta:
        model = PMSchedule
        fields = [
            'task_name', 'asset', 'frequency', 'next_due',
            'assigned_to', 'estimated_hours', 'instructions', 'status'
        ]
        widgets = {
            'next_due':     forms.DateInput(attrs={'type': 'date'}),
            'instructions': forms.Textarea(attrs={'rows': 3}),
        }


class WorkRequestForm(forms.ModelForm):
    class Meta:
        model = WorkRequest
        fields = [
            'title', 'asset', 'location', 'alarm_type', 'alarm_code',
            'breakdown_type', 'priority', 'description', 'symptoms',
            'production_impact', 'reported_by', 'reporter_phone',
            'reporter_department', 'breakdown_time', 'downtime_hours',
        ]
        widgets = {
            'breakdown_time':    forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description':       forms.Textarea(attrs={'rows': 3}),
            'symptoms':          forms.Textarea(attrs={'rows': 2}),
            'production_impact': forms.Textarea(attrs={'rows': 2}),
        }


class WRConvertForm(forms.Form):
    """Form shown when converting a Work Request to a Work Order."""
    assigned_to     = forms.CharField(max_length=100, label='Assigned Technician')
    due_date        = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='Due Date')
    estimated_hours = forms.DecimalField(max_digits=5, decimal_places=1, label='Estimated Hours')
    wo_type         = forms.ChoiceField(choices=WorkOrder.TYPE_CHOICES, initial='Corrective', label='WO Type')
    priority        = forms.ChoiceField(choices=WorkOrder.PRIORITY_CHOICES, label='Priority')
    labor_cost      = forms.DecimalField(max_digits=10, decimal_places=2, initial=0, required=False, label='Estimated Labor Cost (EGP)')
    review_notes    = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False, label='Review Notes')


class SparePartUsageForm(forms.ModelForm):
    class Meta:
        model = SparePartUsage
        fields = ['part_name', 'part_number', 'quantity', 'unit_cost']


# ── USER MANAGEMENT FORMS ─────────────────────────────────────────────────

ROLE_CHOICES = [
    ('admin',        'Administrator — Full Access'),
    ('section_head', 'Section Head — Full Access'),
    ('engineer',     'Maintenance Engineer'),
    ('technician',   'Technician'),
    ('operator',     'Operator'),
    ('viewer',       'Viewer (Read Only)'),
]

PAGE_HELP = {
    'can_access_dashboard':   'Can view the main dashboard',
    'can_access_assets':      'Can view assets list and details',
    'can_access_workrequest': 'Can view work requests',
    'can_access_workorder':   'Can view work orders',
    'can_access_pm':          'Can view PM schedule',
    'can_access_reports':     'Can view reports and analytics',
    'can_create_wr':          'Can submit new work requests',
    'can_convert_wr':         'Can convert work requests to work orders',
    'can_create_wo':          'Can create and edit work orders',
    'can_close_wo':           'Can update work order status / close WOs',
    'can_manage_assets':      'Can add, edit, and delete assets',
    'can_manage_pm':          'Can add, edit, and delete PM tasks',
}


class UserCreateForm(forms.Form):
    # Account
    username   = forms.CharField(max_length=150, label='Username')
    password   = forms.CharField(widget=forms.PasswordInput, label='Password')
    first_name = forms.CharField(max_length=100, label='First Name')
    last_name  = forms.CharField(max_length=100, label='Last Name', required=False)
    email      = forms.EmailField(required=False, label='Email')

    # Profile
    role        = forms.ChoiceField(choices=ROLE_CHOICES, label='Role')
    employee_id = forms.CharField(max_length=50, required=False, label='Employee ID')
    department  = forms.CharField(max_length=100, required=False, label='Department')
    position    = forms.CharField(max_length=100, required=False, label='Job Position / Title',
                                  help_text='e.g. Senior Maintenance Engineer, Production Supervisor')
    phone       = forms.CharField(max_length=30, required=False, label='Phone')

    # Page Access
    can_access_dashboard   = forms.BooleanField(required=False, initial=True,  label='Dashboard')
    can_access_assets      = forms.BooleanField(required=False, label='Assets')
    can_access_workrequest = forms.BooleanField(required=False, label='Work Requests')
    can_access_workorder   = forms.BooleanField(required=False, label='Work Orders')
    can_access_pm          = forms.BooleanField(required=False, label='PM Schedule')
    can_access_reports     = forms.BooleanField(required=False, label='Reports')

    # Action Permissions
    can_create_wr      = forms.BooleanField(required=False, label='Submit Work Requests')
    can_convert_wr     = forms.BooleanField(required=False, label='Convert WR → WO')
    can_create_wo      = forms.BooleanField(required=False, label='Create/Edit Work Orders')
    can_close_wo       = forms.BooleanField(required=False, label='Close / Update WO Status')
    can_manage_assets  = forms.BooleanField(required=False, label='Add/Edit Assets')
    can_manage_pm      = forms.BooleanField(required=False, label='Manage PM Tasks')
    can_access_safety  = forms.BooleanField(required=False, label='Access Safety Permits')
    can_approve_safety = forms.BooleanField(required=False, label='Approve/Reject Safety Permits')

    # Notification preferences
    notify_wr_new       = forms.BooleanField(required=False, label='New Work Request submitted')
    notify_wr_converted = forms.BooleanField(required=False, label='Work Request converted to WO')
    notify_wr_rejected  = forms.BooleanField(required=False, label='Work Request rejected')
    notify_wo_assigned  = forms.BooleanField(required=False, label='Work Order assigned to me')
    notify_wo_completed = forms.BooleanField(required=False, label='Work Order completed')
    notify_wo_overdue   = forms.BooleanField(required=False, label='Work Order overdue')
    notify_pm_due       = forms.BooleanField(required=False, label='PM Task due soon')
    notify_pm_overdue   = forms.BooleanField(required=False, label='PM Task overdue')
    notify_safety_permit = forms.BooleanField(required=False, label='New Safety Permit needs approval')

    def clean_username(self):
        from django.contrib.auth.models import User
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username already exists.')
        return username


class UserEditForm(forms.Form):
    first_name   = forms.CharField(max_length=100, label='First Name')
    last_name    = forms.CharField(max_length=100, label='Last Name', required=False)
    email        = forms.EmailField(required=False, label='Email')
    new_password = forms.CharField(widget=forms.PasswordInput, required=False,
                                   label='New Password (leave blank to keep current)')
    role         = forms.ChoiceField(choices=ROLE_CHOICES, label='Role')
    employee_id  = forms.CharField(max_length=50, required=False, label='Employee ID')
    department   = forms.CharField(max_length=100, required=False, label='Department')
    position     = forms.CharField(max_length=100, required=False, label='Job Position / Title',
                                   help_text='e.g. Senior Maintenance Engineer')
    phone        = forms.CharField(max_length=30, required=False, label='Phone')
    is_active    = forms.BooleanField(required=False, initial=True, label='Account Active')

    can_access_dashboard   = forms.BooleanField(required=False, label='Dashboard')
    can_access_assets      = forms.BooleanField(required=False, label='Assets')
    can_access_workrequest = forms.BooleanField(required=False, label='Work Requests')
    can_access_workorder   = forms.BooleanField(required=False, label='Work Orders')
    can_access_pm          = forms.BooleanField(required=False, label='PM Schedule')
    can_access_reports     = forms.BooleanField(required=False, label='Reports')

    can_create_wr      = forms.BooleanField(required=False, label='Submit Work Requests')
    can_convert_wr     = forms.BooleanField(required=False, label='Convert WR → WO')
    can_create_wo      = forms.BooleanField(required=False, label='Create/Edit Work Orders')
    can_close_wo       = forms.BooleanField(required=False, label='Close / Update WO Status')
    can_manage_assets  = forms.BooleanField(required=False, label='Add/Edit Assets')
    can_manage_pm      = forms.BooleanField(required=False, label='Manage PM Tasks')
    can_access_safety  = forms.BooleanField(required=False, label='Access Safety Permits')
    can_approve_safety = forms.BooleanField(required=False, label='Approve/Reject Safety Permits')

    notify_wr_new       = forms.BooleanField(required=False, label='New Work Request submitted')
    notify_wr_converted = forms.BooleanField(required=False, label='Work Request converted to WO')
    notify_wr_rejected  = forms.BooleanField(required=False, label='Work Request rejected')
    notify_wo_assigned  = forms.BooleanField(required=False, label='Work Order assigned to me')
    notify_wo_completed = forms.BooleanField(required=False, label='Work Order completed')
    notify_wo_overdue   = forms.BooleanField(required=False, label='Work Order overdue')
    notify_pm_due       = forms.BooleanField(required=False, label='PM Task due soon')
    notify_pm_overdue   = forms.BooleanField(required=False, label='PM Task overdue')
    notify_safety_permit = forms.BooleanField(required=False, label='New Safety Permit needs approval')

    def __init__(self, *args, instance=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if not args and instance:  # Pre-fill on GET
            self.fields['first_name'].initial   = user.first_name if user else ''
            self.fields['last_name'].initial    = user.last_name  if user else ''
            self.fields['email'].initial        = user.email      if user else ''
            self.fields['role'].initial         = instance.role
            self.fields['employee_id'].initial  = instance.employee_id
            self.fields['department'].initial   = instance.department
            self.fields['position'].initial     = instance.position
            self.fields['phone'].initial        = instance.phone
            self.fields['is_active'].initial    = instance.is_active
            for f in ['can_access_dashboard','can_access_assets','can_access_workrequest',
                      'can_access_workorder','can_access_pm','can_access_reports',
                      'can_create_wr','can_convert_wr','can_create_wo',
                      'can_close_wo','can_manage_assets','can_manage_pm',
                      'can_access_safety','can_approve_safety',
                      'notify_wr_new','notify_wr_converted','notify_wr_rejected',
                      'notify_wo_assigned','notify_wo_completed','notify_wo_overdue',
                      'notify_pm_due','notify_pm_overdue','notify_safety_permit']:
                self.fields[f].initial = getattr(instance, f, False)


# ── NEW MODULE FORMS ───────────────────────────────────────────────────────

class PredictiveRecordForm(forms.ModelForm):
    class Meta:
        model = PredictiveRecord
        fields = ['asset','parameter','value','unit','normal_min','normal_max','notes','recorded_by','recorded_at']
        widgets = {'recorded_at': forms.DateTimeInput(attrs={'type':'datetime-local'}),
                   'notes': forms.Textarea(attrs={'rows':2})}


class ProactiveActionForm(forms.ModelForm):
    class Meta:
        model = ProactiveAction
        fields = ['asset','title','action_type','priority','status','trigger_reason',
                  'action_plan','assigned_to','planned_date','estimated_hours','actual_hours',
                  'completed_date','result']
        widgets = {
            'planned_date':    forms.DateInput(attrs={'type':'date'}),
            'completed_date':  forms.DateInput(attrs={'type':'date'}),
            'trigger_reason':  forms.Textarea(attrs={'rows':2}),
            'action_plan':     forms.Textarea(attrs={'rows':3}),
            'result':          forms.Textarea(attrs={'rows':2}),
        }


class BreakdownAnalysisForm(forms.ModelForm):
    class Meta:
        model = BreakdownAnalysis
        fields = ['asset','work_order','work_request','title','failure_date','restored_date',
                  'total_downtime','production_loss','repair_cost','cause_category',
                  'analysis_method','why_1','why_2','why_3','why_4','why_5',
                  'root_cause','corrective_actions','preventive_actions',
                  'lessons_learned','recurrence_risk','analysed_by','approved_by']
        widgets = {
            'failure_date':       forms.DateInput(attrs={'type':'date'}),
            'restored_date':      forms.DateInput(attrs={'type':'date'}),
            'why_1':              forms.Textarea(attrs={'rows':2}),
            'why_2':              forms.Textarea(attrs={'rows':2}),
            'why_3':              forms.Textarea(attrs={'rows':2}),
            'why_4':              forms.Textarea(attrs={'rows':2}),
            'why_5':              forms.Textarea(attrs={'rows':2}),
            'root_cause':         forms.Textarea(attrs={'rows':3}),
            'corrective_actions': forms.Textarea(attrs={'rows':3}),
            'preventive_actions': forms.Textarea(attrs={'rows':3}),
            'lessons_learned':    forms.Textarea(attrs={'rows':2}),
        }


class FacilityForm(forms.ModelForm):
    class Meta:
        model = Facility
        fields = ['code','name','name_ar','facility_type','parent','status',
                  'area_sqm','responsible_person','phone','notes']
        widgets = {'notes': forms.Textarea(attrs={'rows':2}),
                   'name_ar': forms.TextInput(attrs={'dir':'rtl'})}


class FacilityServiceRequestForm(forms.ModelForm):
    class Meta:
        model = FacilityServiceRequest
        fields = ['facility','category','priority','title','description',
                  'reported_by','reporter_phone','assigned_to','due_date','cost','notes']
        widgets = {
            'due_date':    forms.DateInput(attrs={'type':'date'}),
            'description': forms.Textarea(attrs={'rows':3}),
            'notes':       forms.Textarea(attrs={'rows':2}),
        }


# ── ISO MODULE FORMS ───────────────────────────────────────────────────────

from .models import (Instrument, CalibrationRecord, NonConformance,
                     ISODocument, InternalAudit, EnvironmentalAspect)


class InstrumentForm(forms.ModelForm):
    class Meta:
        model = Instrument
        fields = ['instrument_id','name','instrument_type','manufacturer','model_number',
                  'serial_number','range_min','range_max','unit','accuracy','location',
                  'asset','responsible_person','calibration_frequency','last_calibration',
                  'next_calibration','calibration_lab','status','iso_reference','notes']
        widgets = {
            'last_calibration': forms.DateInput(attrs={'type':'date'}),
            'next_calibration': forms.DateInput(attrs={'type':'date'}),
            'notes': forms.Textarea(attrs={'rows':2}),
        }


class CalibrationRecordForm(forms.ModelForm):
    class Meta:
        model = CalibrationRecord
        fields = ['instrument','calibration_date','next_due','performed_by','lab_name',
                  'certificate_number','result','reading_before','reading_after',
                  'reference_standard','temperature_c','humidity_pct','notes']
        widgets = {
            'calibration_date': forms.DateInput(attrs={'type':'date'}),
            'next_due':         forms.DateInput(attrs={'type':'date'}),
            'notes':            forms.Textarea(attrs={'rows':2}),
        }


class NonConformanceForm(forms.ModelForm):
    class Meta:
        model = NonConformance
        fields = ['title','source','grade','iso_standard','iso_clause','department',
                  'description','evidence','immediate_action','root_cause',
                  'corrective_action','preventive_action','status','raised_by',
                  'assigned_to','target_date','completed_date','verified_by',
                  'verified_date','verification_notes','linked_wo']
        widgets = {
            'target_date':      forms.DateInput(attrs={'type':'date'}),
            'completed_date':   forms.DateInput(attrs={'type':'date'}),
            'verified_date':    forms.DateInput(attrs={'type':'date'}),
            'description':      forms.Textarea(attrs={'rows':3}),
            'evidence':         forms.Textarea(attrs={'rows':2}),
            'immediate_action': forms.Textarea(attrs={'rows':2}),
            'root_cause':       forms.Textarea(attrs={'rows':2}),
            'corrective_action':forms.Textarea(attrs={'rows':3}),
            'preventive_action':forms.Textarea(attrs={'rows':2}),
            'verification_notes':forms.Textarea(attrs={'rows':2}),
        }


class ISODocumentForm(forms.ModelForm):
    class Meta:
        model = ISODocument
        fields = ['doc_number','title','doc_type','iso_standard','iso_clause','department',
                  'revision','status','prepared_by','reviewed_by','approved_by',
                  'issue_date','review_date','scope','location','change_summary','notes']
        widgets = {
            'issue_date':     forms.DateInput(attrs={'type':'date'}),
            'review_date':    forms.DateInput(attrs={'type':'date'}),
            'scope':          forms.Textarea(attrs={'rows':2}),
            'change_summary': forms.Textarea(attrs={'rows':2}),
            'notes':          forms.Textarea(attrs={'rows':2}),
        }


class InternalAuditForm(forms.ModelForm):
    class Meta:
        model = InternalAudit
        fields = ['title','iso_standard','audit_type','department','clauses_audited',
                  'lead_auditor','audit_team','auditee','planned_date','actual_date',
                  'duration_hours','status','scope','checklist_notes','summary',
                  'major_nc_count','minor_nc_count','observation_count','ofi_count',
                  'overall_result','next_audit_date']
        widgets = {
            'planned_date':    forms.DateInput(attrs={'type':'date'}),
            'actual_date':     forms.DateInput(attrs={'type':'date'}),
            'next_audit_date': forms.DateInput(attrs={'type':'date'}),
            'scope':           forms.Textarea(attrs={'rows':2}),
            'checklist_notes': forms.Textarea(attrs={'rows':5}),
            'summary':         forms.Textarea(attrs={'rows':3}),
            'audit_team':      forms.Textarea(attrs={'rows':2}),
        }


class EnvironmentalAspectForm(forms.ModelForm):
    class Meta:
        model = EnvironmentalAspect
        fields = ['activity','aspect','impact','condition','department','asset',
                  'severity','probability','detection','legal_requirement',
                  'control_measure','objective','responsible','review_date','notes']
        widgets = {
            'review_date':       forms.DateInput(attrs={'type':'date'}),
            'impact':            forms.TextInput(),
            'legal_requirement': forms.Textarea(attrs={'rows':2}),
            'control_measure':   forms.Textarea(attrs={'rows':2}),
            'objective':         forms.Textarea(attrs={'rows':2}),
            'notes':             forms.Textarea(attrs={'rows':2}),
        }


# ── SAFETY PERMIT FORM ─────────────────────────────────────────────────────

from .models import SafetyPermit

class SafetyPermitForm(forms.ModelForm):
    class Meta:
        model = SafetyPermit
        fields = ['work_order','permit_type','risk_level','work_description','location',
                  'requested_by','workers_involved','supervisor',
                  'hazards_identified','ppe_required','precautions_taken',
                  'isolation_required','isolation_details',
                  'fire_watch_required','gas_test_required','gas_test_result',
                  'valid_from','valid_until']
        widgets = {
            'work_description':   forms.Textarea(attrs={'rows':2}),
            'workers_involved':   forms.Textarea(attrs={'rows':2}),
            'hazards_identified': forms.Textarea(attrs={'rows':2}),
            'ppe_required':       forms.Textarea(attrs={'rows':2}),
            'precautions_taken':  forms.Textarea(attrs={'rows':2}),
            'isolation_details':  forms.Textarea(attrs={'rows':2}),
            'valid_from':  forms.DateTimeInput(attrs={'type':'datetime-local'}),
            'valid_until': forms.DateTimeInput(attrs={'type':'datetime-local'}),
        }


class SafetyPermitApprovalForm(forms.Form):
    decision = forms.ChoiceField(choices=[('Approved','Approve'),('Rejected','Reject')])
    approved_by = forms.CharField(max_length=100, label='Your Name (Safety Officer)')
    approval_notes = forms.CharField(widget=forms.Textarea(attrs={'rows':2}), required=False)
    rejection_reason = forms.CharField(widget=forms.Textarea(attrs={'rows':2}), required=False)


class SafetyPermitCloseForm(forms.Form):
    closed_by = forms.CharField(max_length=100, label='Closed By')
    closure_notes = forms.CharField(widget=forms.Textarea(attrs={'rows':3}),
                                    label='Site Cleared / Closure Notes', required=False)
