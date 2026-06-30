from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q
from datetime import date, timedelta
from .models import (Asset, WorkOrder, PMSchedule, SparePartUsage, WorkRequest,
                     UserProfile, Notification, CompanySettings,
                     PredictiveRecord, ProactiveAction, BreakdownAnalysis,
                     Facility, FacilityServiceRequest,
                     Instrument, CalibrationRecord, NonConformance,
                     ISODocument, InternalAudit, EnvironmentalAspect,
                     SafetyPermit)
from .forms import (AssetForm, WorkOrderForm, PMScheduleForm, SparePartUsageForm,
                    WorkRequestForm, WRConvertForm, UserCreateForm, UserEditForm,
                    CompanySettingsForm, PredictiveRecordForm, ProactiveActionForm,
                    BreakdownAnalysisForm, FacilityForm, FacilityServiceRequestForm,
                    InstrumentForm, CalibrationRecordForm, NonConformanceForm,
                    ISODocumentForm, InternalAuditForm, EnvironmentalAspectForm,
                    SafetyPermitForm, SafetyPermitApprovalForm, SafetyPermitCloseForm)
from .decorators import require_access, admin_only
from . import notifications as notif_service


@login_required
def custom_logout(request):
    """Logout via GET or POST — fixes Django 5 restriction."""
    from django.contrib.auth import logout
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    today = date.today()
    total_assets   = Asset.objects.count()
    open_wo        = WorkOrder.objects.filter(status__in=['Open', 'In Progress']).count()
    overdue_wo     = WorkOrder.objects.filter(
        due_date__lt=today, status__in=['Open', 'In Progress', 'On Hold']
    ).count()
    completed_this_month = WorkOrder.objects.filter(
        status='Completed',
        completed_date__month=today.month,
        completed_date__year=today.year
    ).count()
    critical_wo = WorkOrder.objects.filter(priority='Critical', status__in=['Open', 'In Progress']).count()
    recent_wos  = WorkOrder.objects.select_related('asset').order_by('-created_at')[:6]
    upcoming_pm = PMSchedule.objects.filter(
        status='Active', next_due__gte=today
    ).select_related('asset').order_by('next_due')[:6]
    overdue_pm  = PMSchedule.objects.filter(
        status='Active', next_due__lt=today
    ).select_related('asset').count()

    new_wr      = WorkRequest.objects.filter(status__in=['New', 'Under Review']).count()
    recent_wrs  = WorkRequest.objects.select_related('asset').order_by('-created_at')[:5]

    context = {
        'total_assets': total_assets,
        'open_wo': open_wo,
        'overdue_wo': overdue_wo,
        'completed_this_month': completed_this_month,
        'critical_wo': critical_wo,
        'recent_wos': recent_wos,
        'upcoming_pm': upcoming_pm,
        'overdue_pm': overdue_pm,
        'new_wr': new_wr,
        'recent_wrs': recent_wrs,
        'today': today,
    }
    return render(request, 'maintenance/dashboard.html', context)


# ── ASSETS ─────────────────────────────────────────────────────────────────

@require_access('can_access_assets')
def asset_list(request):
    q        = request.GET.get('q', '')
    category = request.GET.get('category', '')
    status   = request.GET.get('status', '')
    assets   = Asset.objects.all()
    if q:
        assets = assets.filter(Q(name__icontains=q) | Q(asset_id__icontains=q) | Q(location__icontains=q))
    if category:
        assets = assets.filter(category=category)
    if status:
        assets = assets.filter(status=status)
    categories = Asset.CATEGORY_CHOICES
    return render(request, 'maintenance/asset_list.html', {
        'assets': assets, 'q': q,
        'categories': categories,
        'selected_cat': category,
        'selected_status': status,
    })


@require_access('can_access_assets')
def asset_detail(request, pk):
    asset   = get_object_or_404(Asset, pk=pk)
    wos     = asset.work_orders.order_by('-created_at')[:10]
    pm_tasks = asset.pm_schedules.order_by('next_due')
    return render(request, 'maintenance/asset_detail.html', {
        'asset': asset, 'wos': wos, 'pm_tasks': pm_tasks
    })


@require_access('can_manage_assets')
def asset_create(request):
    form = AssetForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Asset added successfully.')
        return redirect('asset_list')
    return render(request, 'maintenance/asset_form.html', {'form': form, 'title': 'Add Asset'})


@require_access('can_manage_assets')
def asset_edit(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    form  = AssetForm(request.POST or None, instance=asset)
    if form.is_valid():
        form.save()
        messages.success(request, 'Asset updated.')
        return redirect('asset_detail', pk=pk)
    return render(request, 'maintenance/asset_form.html', {'form': form, 'title': 'Edit Asset'})


@require_access('can_manage_assets')
def asset_delete(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    if request.method == 'POST':
        asset.delete()
        messages.success(request, 'Asset deleted.')
        return redirect('asset_list')
    return render(request, 'maintenance/confirm_delete.html', {'obj': asset, 'type': 'Asset'})


# ── WORK ORDERS ────────────────────────────────────────────────────────────

@require_access('can_access_workorder')
def wo_list(request):
    q        = request.GET.get('q', '')
    priority = request.GET.get('priority', '')
    status   = request.GET.get('status', '')
    wos      = WorkOrder.objects.select_related('asset').all()
    if q:
        wos = wos.filter(Q(wo_number__icontains=q) | Q(title__icontains=q) | Q(assigned_to__icontains=q))
    if priority:
        wos = wos.filter(priority=priority)
    if status:
        wos = wos.filter(status=status)
    today = date.today()
    return render(request, 'maintenance/wo_list.html', {
        'wos': wos, 'q': q,
        'selected_priority': priority,
        'selected_status': status,
        'today': today,
    })


@require_access('can_access_workorder')
def wo_detail(request, pk):
    wo = get_object_or_404(WorkOrder, pk=pk)
    parts = wo.parts.all()
    part_form = SparePartUsageForm()
    if request.method == 'POST' and 'add_part' in request.POST:
        part_form = SparePartUsageForm(request.POST)
        if part_form.is_valid():
            part = part_form.save(commit=False)
            part.work_order = wo
            part.save()
            wo.parts_cost = sum(p.total_cost() for p in wo.parts.all())
            wo.save()
            messages.success(request, 'Part added.')
            return redirect('wo_detail', pk=pk)
    return render(request, 'maintenance/wo_detail.html', {
        'wo': wo, 'parts': parts, 'part_form': part_form, 'today': date.today()
    })


@require_access('can_create_wo')
def wo_create(request):
    form = WorkOrderForm(request.POST or None)
    if form.is_valid():
        wo = form.save(commit=False)
        wo.created_by = request.user
        wo.save()
        messages.success(request, f'Work Order {wo.wo_number} created.')
        return redirect('wo_list')
    return render(request, 'maintenance/wo_form.html', {'form': form, 'title': 'New Work Order'})


@require_access('can_create_wo')
def wo_edit(request, pk):
    wo   = get_object_or_404(WorkOrder, pk=pk)
    form = WorkOrderForm(request.POST or None, instance=wo)
    if form.is_valid():
        wo = form.save()
        if wo.status == 'Completed' and not wo.completed_date:
            wo.completed_date = date.today()
            wo.completed_at = timezone.now()
            wo.save()
        messages.success(request, 'Work Order updated.')
        return redirect('wo_detail', pk=pk)
    return render(request, 'maintenance/wo_form.html', {'form': form, 'title': 'Edit Work Order'})


@require_access('can_create_wo')
def wo_delete(request, pk):
    wo = get_object_or_404(WorkOrder, pk=pk)
    if request.method == 'POST':
        wo.delete()
        messages.success(request, 'Work Order deleted.')
        return redirect('wo_list')
    return render(request, 'maintenance/confirm_delete.html', {'obj': wo, 'type': 'Work Order'})


@require_access('can_close_wo')
def wo_update_status(request, pk):
    wo = get_object_or_404(WorkOrder, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(WorkOrder.STATUS_CHOICES):
            wo.status = new_status
            if new_status == 'Completed' and not wo.completed_date:
                wo.completed_date = date.today()
                wo.completed_at = timezone.now()
            wo.save()
            if new_status == 'Completed':
                notif_service.notify_wo_completed(wo, completed_by=request.user)
            messages.success(request, f'Status updated to {new_status}.')
    return redirect('wo_detail', pk=pk)


# ── PM SCHEDULE ────────────────────────────────────────────────────────────

@require_access('can_access_pm')
def pm_list(request):
    today  = date.today()
    status = request.GET.get('status', '')
    pms    = PMSchedule.objects.select_related('asset').filter(status='Active')
    if status == 'overdue':
        pms = pms.filter(next_due__lt=today)
    elif status == 'upcoming':
        pms = pms.filter(next_due__gte=today, next_due__lte=today + timedelta(days=30))
    return render(request, 'maintenance/pm_list.html', {
        'pms': pms, 'today': today, 'selected_status': status
    })


@require_access('can_manage_pm')
def pm_create(request):
    form = PMScheduleForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'PM Task created.')
        return redirect('pm_list')
    return render(request, 'maintenance/pm_form.html', {'form': form, 'title': 'Add PM Task'})


@require_access('can_manage_pm')
def pm_edit(request, pk):
    pm   = get_object_or_404(PMSchedule, pk=pk)
    form = PMScheduleForm(request.POST or None, instance=pm)
    if form.is_valid():
        form.save()
        messages.success(request, 'PM Task updated.')
        return redirect('pm_list')
    return render(request, 'maintenance/pm_form.html', {'form': form, 'title': 'Edit PM Task'})


@require_access('can_manage_pm')
def pm_complete(request, pk):
    pm = get_object_or_404(PMSchedule, pk=pk)
    if request.method == 'POST':
        pm.last_completed = date.today()
        freq_map = {
            'Daily': 1, 'Weekly': 7, 'Monthly': 30,
            'Quarterly': 91, 'Semi-Annual': 182, 'Annual': 365
        }
        days = freq_map.get(pm.frequency, 30)
        pm.next_due = date.today() + timedelta(days=days)
        pm.save()
        # Update asset last PM date
        pm.asset.last_pm_date = date.today()
        pm.asset.save()
        messages.success(request, f'PM Task marked complete. Next due: {pm.next_due}')
    return redirect('pm_list')


@require_access('can_manage_pm')
def pm_delete(request, pk):
    pm = get_object_or_404(PMSchedule, pk=pk)
    if request.method == 'POST':
        pm.delete()
        messages.success(request, 'PM Task deleted.')
        return redirect('pm_list')
    return render(request, 'maintenance/confirm_delete.html', {'obj': pm, 'type': 'PM Task'})


# ── REPORTS ────────────────────────────────────────────────────────────────

@require_access('can_access_reports')
def reports(request):
    today = date.today()
    # WO stats
    total_wo   = WorkOrder.objects.count()
    by_status  = WorkOrder.objects.values('status').annotate(count=Count('id'))
    by_priority = WorkOrder.objects.values('priority').annotate(count=Count('id'))
    by_category = WorkOrder.objects.values('asset__category').annotate(count=Count('id'))
    # Asset stats
    by_asset_status = Asset.objects.values('status').annotate(count=Count('id'))
    # Completion rate
    completed  = WorkOrder.objects.filter(status='Completed').count()
    comp_rate  = round((completed / total_wo * 100) if total_wo > 0 else 0, 1)
    # Overdue
    overdue_count = WorkOrder.objects.filter(
        due_date__lt=today, status__in=['Open', 'In Progress']
    ).count()
    # Monthly WOs (last 6 months)
    monthly = []
    for i in range(5, -1, -1):
        m = today.replace(day=1) - timedelta(days=i * 30)
        cnt = WorkOrder.objects.filter(created_at__year=m.year, created_at__month=m.month).count()
        monthly.append({'month': m.strftime('%b %Y'), 'count': cnt})

    # ── Cycle Time Analytics (creation → completion) ──
    completed_wos_with_time = WorkOrder.objects.filter(
        status='Completed', completed_at__isnull=False
    )
    cycle_times = [wo.cycle_time_hours() for wo in completed_wos_with_time if wo.cycle_time_hours() is not None]

    if cycle_times:
        avg_cycle_hours = round(sum(cycle_times) / len(cycle_times), 1)
        fastest_hours   = round(min(cycle_times), 1)
        slowest_hours   = round(max(cycle_times), 1)
    else:
        avg_cycle_hours = fastest_hours = slowest_hours = None

    def fmt_hours(h):
        if h is None:
            return None
        days, rem = divmod(int(h * 60), 1440)
        hrs, mins = divmod(rem, 60)
        if days > 0:
            return f"{days}d {hrs}h"
        elif hrs > 0:
            return f"{hrs}h {mins}m"
        return f"{mins}m"

    # Average cycle time broken down by priority
    cycle_by_priority = []
    for pr_value, pr_label in WorkOrder.PRIORITY_CHOICES:
        wos = WorkOrder.objects.filter(status='Completed', completed_at__isnull=False, priority=pr_value)
        times = [w.cycle_time_hours() for w in wos if w.cycle_time_hours() is not None]
        if times:
            cycle_by_priority.append({
                'priority': pr_label,
                'avg_display': fmt_hours(sum(times) / len(times)),
                'count': len(times),
            })

    # Slowest 5 completed work orders (for investigation)
    slowest_wos = sorted(
        [w for w in completed_wos_with_time if w.cycle_time_hours() is not None],
        key=lambda w: w.cycle_time_hours(), reverse=True
    )[:5]

    # ── Safety Permit Response Time Analytics (created → approved/rejected) ──
    decided_permits = SafetyPermit.objects.filter(approved_at__isnull=False)
    permit_times = [p.response_time_hours() for p in decided_permits if p.response_time_hours() is not None]

    if permit_times:
        avg_permit_hours     = round(sum(permit_times) / len(permit_times), 2)
        fastest_permit_hours = round(min(permit_times), 2)
        slowest_permit_hours = round(max(permit_times), 2)
    else:
        avg_permit_hours = fastest_permit_hours = slowest_permit_hours = None

    # Average permit response time broken down by risk level
    permit_by_risk = []
    for rk_value, rk_label in SafetyPermit.RISK_LEVEL_CHOICES:
        perms = SafetyPermit.objects.filter(approved_at__isnull=False, risk_level=rk_value)
        times = [p.response_time_hours() for p in perms if p.response_time_hours() is not None]
        if times:
            permit_by_risk.append({
                'risk': rk_label,
                'avg_display': fmt_hours(sum(times) / len(times)),
                'count': len(times),
            })

    # Slowest 5 permit approvals (for investigation — safety bottlenecks)
    slowest_permits = sorted(
        [p for p in decided_permits if p.response_time_hours() is not None],
        key=lambda p: p.response_time_hours(), reverse=True
    )[:5]

    pending_permits_count = SafetyPermit.objects.filter(status='Pending').count()

    context = {
        'total_wo': total_wo,
        'by_status': list(by_status),
        'by_priority': list(by_priority),
        'by_category': list(by_category),
        'by_asset_status': list(by_asset_status),
        'comp_rate': comp_rate,
        'overdue_count': overdue_count,
        'monthly': monthly,
        'total_assets': Asset.objects.count(),
        'active_pm': PMSchedule.objects.filter(status='Active').count(),
        # Cycle time
        'avg_cycle_display': fmt_hours(avg_cycle_hours),
        'fastest_cycle_display': fmt_hours(fastest_hours),
        'slowest_cycle_display': fmt_hours(slowest_hours),
        'cycle_time_count': len(cycle_times),
        'cycle_by_priority': cycle_by_priority,
        'slowest_wos': slowest_wos,
        # Safety permit response time
        'avg_permit_display': fmt_hours(avg_permit_hours),
        'fastest_permit_display': fmt_hours(fastest_permit_hours),
        'slowest_permit_display': fmt_hours(slowest_permit_hours),
        'permit_time_count': len(permit_times),
        'permit_by_risk': permit_by_risk,
        'slowest_permits': slowest_permits,
        'pending_permits_count': pending_permits_count,
    }
    return render(request, 'maintenance/reports.html', context)


# ── WORK REQUESTS ──────────────────────────────────────────────────────────

@require_access('can_access_workrequest')
def wr_list(request):
    q        = request.GET.get('q', '')
    priority = request.GET.get('priority', '')
    status   = request.GET.get('status', '')
    wrs      = WorkRequest.objects.select_related('asset').all()
    if q:
        wrs = wrs.filter(
            Q(wr_number__icontains=q) | Q(title__icontains=q) |
            Q(reported_by__icontains=q) | Q(alarm_code__icontains=q)
        )
    if priority:
        wrs = wrs.filter(priority=priority)
    if status:
        wrs = wrs.filter(status=status)
    return render(request, 'maintenance/wr_list.html', {
        'wrs': wrs, 'q': q,
        'selected_priority': priority,
        'selected_status': status,
    })


@require_access('can_access_workrequest')
def wr_detail(request, pk):
    wr = get_object_or_404(WorkRequest, pk=pk)
    return render(request, 'maintenance/wr_detail.html', {'wr': wr})


@require_access('can_create_wr')
def wr_create(request):
    form = WorkRequestForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            wr = form.save(commit=False)
            wr.created_by = request.user
            wr.save()
            # Mark asset as offline if full breakdown
            if wr.breakdown_type == 'Full Breakdown' and wr.asset:
                wr.asset.status = 'Offline'
                wr.asset.save()
            # Fire notification to maintenance team
            notif_service.notify_wr_created(wr, created_by=request.user)
            messages.success(request, f'Work Request {wr.wr_number} submitted successfully.')
            return redirect('wr_list')
    return render(request, 'maintenance/wr_form.html', {'form': form, 'title': 'New Work Request'})


@require_access('can_create_wr')
def wr_edit(request, pk):
    wr   = get_object_or_404(WorkRequest, pk=pk)
    form = WorkRequestForm(request.POST or None, instance=wr)
    if form.is_valid():
        form.save()
        messages.success(request, 'Work Request updated.')
        return redirect('wr_detail', pk=pk)
    return render(request, 'maintenance/wr_form.html', {'form': form, 'title': 'Edit Work Request'})


@require_access('can_create_wr')
def wr_delete(request, pk):
    wr = get_object_or_404(WorkRequest, pk=pk)
    if request.method == 'POST':
        wr.delete()
        messages.success(request, 'Work Request deleted.')
        return redirect('wr_list')
    return render(request, 'maintenance/confirm_delete.html', {'obj': wr, 'type': 'Work Request'})


@require_access('can_access_workrequest')
def wr_update_status(request, pk):
    wr = get_object_or_404(WorkRequest, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(WorkRequest.STATUS_CHOICES):
            wr.status = new_status
            wr.reviewed_by = request.user
            wr.reviewed_at = timezone.now()
            wr.save()
            if new_status == 'Rejected':
                notif_service.notify_wr_rejected(wr, rejected_by=request.user)
            messages.success(request, f'Status updated to {new_status}.')
    return redirect('wr_detail', pk=pk)


@require_access('can_convert_wr')
def wr_convert(request, pk):
    """Convert a Work Request into a Work Order."""
    wr = get_object_or_404(WorkRequest, pk=pk)

    if wr.status == 'Converted':
        messages.warning(request, 'This Work Request is already converted to a Work Order.')
        return redirect('wr_detail', pk=pk)

    # Pre-fill the convert form with data from the work request
    initial = {
        'priority':        wr.priority if wr.priority in ['Critical', 'Medium', 'Low'] else 'Medium',
        'wo_type':         'Emergency' if wr.priority == 'Critical' else 'Corrective',
        'estimated_hours': wr.downtime_hours or 2,
        'due_date':        date.today() + timedelta(days=1 if wr.priority == 'Critical' else 3),
    }

    form = WRConvertForm(request.POST or None, initial=initial)

    if request.method == 'POST' and form.is_valid():
        # Build description combining WR data
        description = f"""
CONVERTED FROM WORK REQUEST: {wr.wr_number}
{'='*50}
ALARM TYPE    : {wr.alarm_type}
ALARM CODE    : {wr.alarm_code or 'N/A'}
BREAKDOWN TYPE: {wr.breakdown_type}
BREAKDOWN TIME: {wr.breakdown_time.strftime('%d/%m/%Y %H:%M')}
DOWNTIME      : {wr.downtime_hours or 'N/A'} hours
LOCATION      : {wr.location or (wr.asset.location if wr.asset else 'N/A')}
REPORTED BY   : {wr.reported_by} ({wr.reporter_department or 'N/A'}) — {wr.reporter_phone or ''}
{'='*50}
PROBLEM DESCRIPTION:
{wr.description}

SYMPTOMS OBSERVED:
{wr.symptoms or 'N/A'}

PRODUCTION IMPACT:
{wr.production_impact or 'N/A'}
        """.strip()

        wo = WorkOrder.objects.create(
            title           = f"[{wr.alarm_type}] {wr.title}",
            asset           = wr.asset,
            wo_type         = form.cleaned_data['wo_type'],
            priority        = form.cleaned_data['priority'],
            status          = 'Open',
            assigned_to     = form.cleaned_data['assigned_to'],
            due_date        = form.cleaned_data['due_date'],
            estimated_hours = form.cleaned_data['estimated_hours'],
            labor_cost      = form.cleaned_data.get('labor_cost') or 0,
            description     = description,
            notes           = form.cleaned_data.get('review_notes', ''),
            created_by      = request.user,
        )

        # Link WR to WO and mark as converted
        wr.converted_to_wo = wo
        wr.status          = 'Converted'
        wr.reviewed_by     = request.user
        wr.reviewed_at     = timezone.now()
        wr.review_notes    = form.cleaned_data.get('review_notes', '')
        wr.save()

        # Update asset status to Under Maintenance
        if wr.asset:
            wr.asset.status = 'Under Maintenance'
            wr.asset.save()

        messages.success(request, f'✅ Work Request {wr.wr_number} converted to {wo.wo_number} successfully!')
        # Fire notifications
        notif_service.notify_wr_converted(wr, wo, converted_by=request.user)
        return redirect('wo_detail', pk=wo.pk)

    return render(request, 'maintenance/wr_convert.html', {
        'wr': wr,
        'form': form,
    })


# ── USER MANAGEMENT (Admin Only) ───────────────────────────────────────────

@admin_only
def user_list(request):
    users = User.objects.select_related('profile').order_by('username')
    return render(request, 'maintenance/user_list.html', {'users': users})


@admin_only
def user_create(request):
    form = UserCreateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = User.objects.create_user(
            username   = form.cleaned_data['username'],
            password   = form.cleaned_data['password'],
            first_name = form.cleaned_data['first_name'],
            last_name  = form.cleaned_data['last_name'],
            email      = form.cleaned_data['email'],
            is_staff   = form.cleaned_data['role'] == 'admin',
        )
        role = form.cleaned_data['role']
        profile = UserProfile(
            user          = user,
            role          = role,
            employee_id   = form.cleaned_data.get('employee_id', ''),
            department    = form.cleaned_data.get('department', ''),
            position      = form.cleaned_data.get('position', ''),
            phone         = form.cleaned_data.get('phone', ''),
            is_active     = True,
            # page access
            can_access_dashboard   = form.cleaned_data.get('can_access_dashboard', True),
            can_access_assets      = form.cleaned_data.get('can_access_assets', False),
            can_access_workrequest = form.cleaned_data.get('can_access_workrequest', False),
            can_access_workorder   = form.cleaned_data.get('can_access_workorder', False),
            can_access_pm          = form.cleaned_data.get('can_access_pm', False),
            can_access_reports     = form.cleaned_data.get('can_access_reports', False),
            # action permissions
            can_create_wr     = form.cleaned_data.get('can_create_wr', False),
            can_convert_wr    = form.cleaned_data.get('can_convert_wr', False),
            can_create_wo     = form.cleaned_data.get('can_create_wo', False),
            can_close_wo      = form.cleaned_data.get('can_close_wo', False),
            can_manage_assets = form.cleaned_data.get('can_manage_assets', False),
            can_manage_pm     = form.cleaned_data.get('can_manage_pm', False),
            can_access_safety  = form.cleaned_data.get('can_access_safety', False),
            can_approve_safety = form.cleaned_data.get('can_approve_safety', False),
            # notifications
            notify_wr_new       = form.cleaned_data.get('notify_wr_new', False),
            notify_wr_converted = form.cleaned_data.get('notify_wr_converted', False),
            notify_wr_rejected  = form.cleaned_data.get('notify_wr_rejected', False),
            notify_wo_assigned  = form.cleaned_data.get('notify_wo_assigned', False),
            notify_wo_completed = form.cleaned_data.get('notify_wo_completed', False),
            notify_wo_overdue   = form.cleaned_data.get('notify_wo_overdue', False),
            notify_pm_due       = form.cleaned_data.get('notify_pm_due', False),
            notify_pm_overdue   = form.cleaned_data.get('notify_pm_overdue', False),
            notify_safety_permit = form.cleaned_data.get('notify_safety_permit', False),
        )
        profile.save()
        messages.success(request, f'✅ User "{user.username}" created successfully.')
        return redirect('user_list')
    return render(request, 'maintenance/user_form.html', {'form': form, 'title': 'Add New User', 'is_create': True})


@admin_only
def user_edit(request, pk):
    user    = get_object_or_404(User, pk=pk)
    profile, _ = UserProfile.objects.get_or_create(user=user)
    form    = UserEditForm(request.POST or None, instance=profile, user=user)
    if request.method == 'POST' and form.is_valid():
        # Update User fields
        user.first_name = form.cleaned_data['first_name']
        user.last_name  = form.cleaned_data['last_name']
        user.email      = form.cleaned_data['email']
        user.is_staff   = form.cleaned_data['role'] == 'admin'
        new_password    = form.cleaned_data.get('new_password')
        if new_password:
            user.set_password(new_password)
        user.save()
        # Update profile
        profile.role          = form.cleaned_data['role']
        profile.employee_id   = form.cleaned_data.get('employee_id', '')
        profile.department    = form.cleaned_data.get('department', '')
        profile.position      = form.cleaned_data.get('position', '')
        profile.phone         = form.cleaned_data.get('phone', '')
        profile.is_active     = form.cleaned_data.get('is_active', True)
        # Page access
        for f in ['can_access_dashboard','can_access_assets','can_access_workrequest',
                  'can_access_workorder','can_access_pm','can_access_reports']:
            setattr(profile, f, form.cleaned_data.get(f, False))
        # Action permissions
        for f in ['can_create_wr','can_convert_wr','can_create_wo',
                  'can_close_wo','can_manage_assets','can_manage_pm',
                  'can_access_safety','can_approve_safety']:
            setattr(profile, f, form.cleaned_data.get(f, False))
        # Notification preferences
        for f in ['notify_wr_new','notify_wr_converted','notify_wr_rejected',
                  'notify_wo_assigned','notify_wo_completed','notify_wo_overdue',
                  'notify_pm_due','notify_pm_overdue','notify_safety_permit']:
            setattr(profile, f, form.cleaned_data.get(f, False))
        profile.save()
        messages.success(request, f'✅ User "{user.username}" updated.')
        return redirect('user_list')
    return render(request, 'maintenance/user_form.html', {
        'form': form, 'title': f'Edit User — {user.username}',
        'edit_user': user, 'is_create': False
    })


@admin_only
def user_toggle_active(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, 'You cannot deactivate your own account.')
        return redirect('user_list')
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.is_active = not profile.is_active
    profile.save()
    state = 'activated' if profile.is_active else 'deactivated'
    messages.success(request, f'User "{user.username}" {state}.')
    return redirect('user_list')


@admin_only
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('user_list')
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User "{username}" deleted.')
        return redirect('user_list')
    return render(request, 'maintenance/confirm_delete.html', {'obj': user, 'type': 'User'})


@admin_only
def user_apply_role(request, pk):
    """AJAX-friendly: apply role defaults to a user's permissions."""
    user    = get_object_or_404(User, pk=pk)
    profile, _ = UserProfile.objects.get_or_create(user=user)
    role    = request.POST.get('role', profile.role)
    profile.role = role
    profile.apply_role_defaults()
    profile.save()
    user.is_staff = (role == 'admin')
    user.save()
    messages.success(request, f'Role defaults applied for "{user.username}".')
    return redirect('user_edit', pk=pk)


# ── NOTIFICATIONS ──────────────────────────────────────────────────────────

@login_required
def notification_list(request):
    notifs = request.user.notifications.all()
    # Mark all as read when opening the page
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'maintenance/notification_list.html', {'notifs': notifs})


@login_required
def notification_mark_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notif.is_read = True
    notif.save()
    if notif.link:
        return redirect(notif.link)
    return redirect('notification_list')


@login_required
def notification_mark_all_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    messages.success(request, 'All notifications marked as read.')
    return redirect('notification_list')


@login_required
def notification_delete(request, pk):
    notif = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notif.delete()
    return redirect('notification_list')


@login_required
def notification_count_api(request):
    """Simple JSON endpoint polled every 30s by the bell icon."""
    from django.http import JsonResponse
    count  = request.user.notifications.filter(is_read=False).count()
    recent_qs = request.user.notifications.filter(is_read=False).order_by('-created_at')[:5]
    recent = []
    for n in recent_qs:
        recent.append({
            'id':         n.id,
            'title':      n.title,
            'message':    n.message,
            'notif_type': n.notif_type,
            'priority':   n.priority,
            'link':       n.link,
            'created_at': n.created_at.strftime('%d/%m %H:%M'),
        })
    return JsonResponse({'count': count, 'recent': recent})


# ── COMPANY SETTINGS (Admin Only) ─────────────────────────────────────────

@admin_only
def company_settings_view(request):
    company = CompanySettings.get()
    form = CompanySettingsForm(request.POST or None, instance=company)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.updated_by = request.user
        obj.save()
        messages.success(request, '✅ Company settings saved successfully.')
        return redirect('company_settings')
    return render(request, 'maintenance/company_settings.html', {
        'form': form, 'company': company
    })


# ── BACKUP & RESTORE (Admin Only) ─────────────────────────────────────────

@admin_only
def backup_download(request):
    """Download the entire SQLite database as a .db file."""
    import os
    from django.http import FileResponse, Http404
    from django.conf import settings as django_settings

    db_path = django_settings.DATABASES['default']['NAME']
    if not os.path.exists(db_path):
        raise Http404("Database file not found.")

    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename  = f'CMMS_Backup_{timestamp}.db'

    response = FileResponse(open(db_path, 'rb'), content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@admin_only
def backup_export_json(request):
    """Export all data as a JSON file — human readable backup."""
    import json
    from django.http import HttpResponse
    from django.core import serializers
    from datetime import datetime

    # Collect all models
    all_data = {}
    models_to_export = [
        ('assets',        Asset.objects.all()),
        ('work_orders',   WorkOrder.objects.all()),
        ('work_requests', WorkRequest.objects.all()),
        ('pm_schedules',  PMSchedule.objects.all()),
        ('spare_parts',   SparePartUsage.objects.all()),
        ('notifications', Notification.objects.all()),
        ('user_profiles', UserProfile.objects.select_related('user').all()),
        ('company',       CompanySettings.objects.all()),
    ]

    export = {
        'exported_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'exported_by': request.user.username,
        'system':      'MaintenePro CMMS',
        'data': {}
    }

    for key, queryset in models_to_export:
        export['data'][key] = json.loads(serializers.serialize('json', queryset))

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename  = f'CMMS_Export_{timestamp}.json'

    response = HttpResponse(
        json.dumps(export, indent=2, ensure_ascii=False),
        content_type='application/json; charset=utf-8'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@admin_only
def backup_export_excel(request):
    """Export key data as Excel file — easy to read and share."""
    import io
    import zipfile
    from django.http import HttpResponse
    from datetime import datetime

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Build CSV content for each table
    import csv

    output = io.BytesIO()

    # We'll create a zip with multiple CSV files
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zf:

        # Assets CSV
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(['Asset ID','Name','Category','Location','Status','Manufacturer','Model','Serial','Last PM','Notes'])
        for a in Asset.objects.all():
            w.writerow([a.asset_id, a.name, a.category, a.location, a.status,
                        a.manufacturer, a.model_number, a.serial_number,
                        a.last_pm_date or '', a.notes])
        zf.writestr(f'01_Assets.csv', buf.getvalue())

        # Work Orders CSV
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(['WO Number','Title','Asset','Type','Priority','Status','Assigned To',
                    'Due Date','Completed Date','Est Hours','Actual Hours','Parts Cost','Labor Cost','Description'])
        for wo in WorkOrder.objects.select_related('asset').all():
            w.writerow([wo.wo_number, wo.title, wo.asset.name if wo.asset else '',
                        wo.wo_type, wo.priority, wo.status, wo.assigned_to,
                        wo.due_date or '', wo.completed_date or '',
                        wo.estimated_hours or '', wo.actual_hours or '',
                        wo.parts_cost, wo.labor_cost, wo.description])
        zf.writestr(f'02_WorkOrders.csv', buf.getvalue())

        # Work Requests CSV
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(['WR Number','Title','Asset','Alarm Type','Alarm Code','Breakdown Type',
                    'Priority','Status','Reported By','Department','Phone',
                    'Breakdown Time','Downtime Hours','Description','Production Impact'])
        for wr in WorkRequest.objects.select_related('asset').all():
            w.writerow([wr.wr_number, wr.title, wr.asset.name if wr.asset else '',
                        wr.alarm_type, wr.alarm_code, wr.breakdown_type,
                        wr.priority, wr.status, wr.reported_by,
                        wr.reporter_department, wr.reporter_phone,
                        wr.breakdown_time.strftime('%Y-%m-%d %H:%M'),
                        wr.downtime_hours or '', wr.description, wr.production_impact])
        zf.writestr(f'03_WorkRequests.csv', buf.getvalue())

        # PM Schedule CSV
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(['Task Name','Asset','Frequency','Next Due','Assigned To','Est Hours','Status','Last Completed'])
        for pm in PMSchedule.objects.select_related('asset').all():
            w.writerow([pm.task_name, pm.asset.name if pm.asset else '',
                        pm.frequency, pm.next_due, pm.assigned_to,
                        pm.estimated_hours, pm.status, pm.last_completed or ''])
        zf.writestr(f'04_PMSchedule.csv', buf.getvalue())

        # Spare Parts CSV
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(['Work Order','Part Name','Part Number','Quantity','Unit Cost','Total Cost'])
        for p in SparePartUsage.objects.select_related('work_order').all():
            w.writerow([p.work_order.wo_number, p.part_name, p.part_number,
                        p.quantity, p.unit_cost, p.total_cost()])
        zf.writestr(f'05_SpareParts.csv', buf.getvalue())

        # Users CSV
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(['Username','Full Name','Email','Role','Position','Department','Phone','Employee ID','Active'])
        for p in UserProfile.objects.select_related('user').all():
            w.writerow([p.user.username, p.user.get_full_name(), p.user.email,
                        p.role, p.position, p.department, p.phone,
                        p.employee_id, 'Yes' if p.is_active else 'No'])
        zf.writestr(f'06_Users.csv', buf.getvalue())

    output.seek(0)
    filename = f'CMMS_Excel_Export_{timestamp}.zip'
    response = HttpResponse(output.read(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@admin_only
def backup_page(request):
    """Backup & Restore dashboard page."""
    import os
    from django.conf import settings as django_settings
    from datetime import datetime

    db_path = django_settings.DATABASES['default']['NAME']
    db_size  = 0
    db_modified = None
    if os.path.exists(db_path):
        db_size     = os.path.getsize(db_path)
        db_modified = datetime.fromtimestamp(os.path.getmtime(db_path))

    stats = {
        'assets':        Asset.objects.count(),
        'work_orders':   WorkOrder.objects.count(),
        'work_requests': WorkRequest.objects.count(),
        'pm_schedules':  PMSchedule.objects.count(),
        'spare_parts':   SparePartUsage.objects.count(),
        'users':         UserProfile.objects.count(),
        'notifications': Notification.objects.count(),
        'db_size_kb':    round(db_size / 1024, 1),
        'db_size_mb':    round(db_size / 1024 / 1024, 2),
        'db_modified':   db_modified,
        'db_path':       str(db_path),
    }
    return render(request, 'maintenance/backup.html', {'stats': stats})


# ── PREDICTIVE MAINTENANCE ─────────────────────────────────────────────────

@require_access('can_access_assets')
def predictive_list(request):
    records = PredictiveRecord.objects.select_related('asset').order_by('-recorded_at')
    asset_filter = request.GET.get('asset', '')
    condition_filter = request.GET.get('condition', '')
    if asset_filter:
        records = records.filter(asset__id=asset_filter)
    if condition_filter:
        records = records.filter(condition=condition_filter)
    assets = Asset.objects.all()
    # Summary stats
    critical = PredictiveRecord.objects.filter(condition='Critical').count()
    warning  = PredictiveRecord.objects.filter(condition='Warning').count()
    return render(request, 'maintenance/predictive_list.html', {
        'records': records, 'assets': assets,
        'critical': critical, 'warning': warning,
        'selected_asset': asset_filter, 'selected_condition': condition_filter,
    })


@require_access('can_manage_assets')
def predictive_create(request):
    asset_id = request.GET.get('asset', '')
    initial = {'asset': asset_id} if asset_id else {}
    form = PredictiveRecordForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        record = form.save(commit=False)
        record.condition = record.calculate_condition()
        record.save()
        # Auto-create proactive action if condition is bad
        if record.condition in ['Warning', 'Critical']:
            ProactiveAction.objects.create(
                asset         = record.asset,
                title         = f'[AUTO] {record.condition} detected — {record.parameter} on {record.asset.name}',
                action_type   = 'Inspection',
                priority      = 'Critical' if record.condition == 'Critical' else 'High',
                status        = 'Planned',
                trigger_reason = f'Sensor reading: {record.parameter} = {record.value} {record.unit}\nNormal range: {record.normal_min} – {record.normal_max}',
                planned_date  = date.today() + timedelta(days=1),
                created_by    = request.user,
            )
            messages.warning(request, f'⚠️ {record.condition} condition detected! A proactive action has been created automatically.')
        else:
            messages.success(request, 'Reading recorded successfully.')
        return redirect('predictive_list')
    return render(request, 'maintenance/predictive_form.html', {'form': form, 'title': 'Add Predictive Reading'})


@require_access('can_manage_assets')
def predictive_delete(request, pk):
    record = get_object_or_404(PredictiveRecord, pk=pk)
    if request.method == 'POST':
        record.delete()
        messages.success(request, 'Record deleted.')
    return redirect('predictive_list')


# ── PROACTIVE MAINTENANCE ──────────────────────────────────────────────────

@require_access('can_access_workorder')
def proactive_list(request):
    actions = ProactiveAction.objects.select_related('asset').all()
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    if status_filter:
        actions = actions.filter(status=status_filter)
    if priority_filter:
        actions = actions.filter(priority=priority_filter)
    return render(request, 'maintenance/proactive_list.html', {
        'actions': actions, 'today': date.today(),
        'selected_status': status_filter, 'selected_priority': priority_filter,
    })


@require_access('can_create_wo')
def proactive_create(request):
    form = ProactiveActionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        action = form.save(commit=False)
        action.created_by = request.user
        action.save()
        messages.success(request, 'Proactive action created.')
        return redirect('proactive_list')
    return render(request, 'maintenance/proactive_form.html', {'form': form, 'title': 'New Proactive Action'})


@require_access('can_create_wo')
def proactive_edit(request, pk):
    action = get_object_or_404(ProactiveAction, pk=pk)
    form = ProactiveActionForm(request.POST or None, instance=action)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Action updated.')
        return redirect('proactive_list')
    return render(request, 'maintenance/proactive_form.html', {'form': form, 'title': 'Edit Proactive Action'})


@require_access('can_create_wo')
def proactive_delete(request, pk):
    action = get_object_or_404(ProactiveAction, pk=pk)
    if request.method == 'POST':
        action.delete()
        messages.success(request, 'Action deleted.')
        return redirect('proactive_list')
    return render(request, 'maintenance/confirm_delete.html', {'obj': action, 'type': 'Proactive Action'})


# ── BREAKDOWN ANALYSIS ─────────────────────────────────────────────────────

@require_access('can_access_reports')
def bda_list(request):
    analyses = BreakdownAnalysis.objects.select_related('asset').all()
    return render(request, 'maintenance/bda_list.html', {'analyses': analyses})


@require_access('can_create_wo')
def bda_create(request):
    wo_id = request.GET.get('wo', '')
    initial = {}
    if wo_id:
        try:
            wo = WorkOrder.objects.get(pk=wo_id)
            initial = {'work_order': wo, 'asset': wo.asset,
                       'title': f'BDA — {wo.title}',
                       'failure_date': wo.due_date or date.today()}
        except WorkOrder.DoesNotExist:
            pass
    form = BreakdownAnalysisForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Breakdown analysis saved.')
        return redirect('bda_list')
    return render(request, 'maintenance/bda_form.html', {'form': form, 'title': 'New Breakdown Analysis'})


@require_access('can_create_wo')
def bda_edit(request, pk):
    analysis = get_object_or_404(BreakdownAnalysis, pk=pk)
    form = BreakdownAnalysisForm(request.POST or None, instance=analysis)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Analysis updated.')
        return redirect('bda_list')
    return render(request, 'maintenance/bda_form.html', {'form': form, 'title': 'Edit Breakdown Analysis'})


@require_access('can_access_reports')
def bda_detail(request, pk):
    analysis = get_object_or_404(BreakdownAnalysis, pk=pk)
    return render(request, 'maintenance/bda_detail.html', {'analysis': analysis})


@require_access('can_create_wo')
def bda_delete(request, pk):
    analysis = get_object_or_404(BreakdownAnalysis, pk=pk)
    if request.method == 'POST':
        analysis.delete()
        messages.success(request, 'Analysis deleted.')
        return redirect('bda_list')
    return render(request, 'maintenance/confirm_delete.html', {'obj': analysis, 'type': 'Breakdown Analysis'})


# ── FACILITIES MANAGEMENT ──────────────────────────────────────────────────

@require_access('can_access_assets')
def facility_list(request):
    facilities = Facility.objects.all()
    sr_open    = FacilityServiceRequest.objects.filter(status='Open').count()
    return render(request, 'maintenance/facility_list.html', {
        'facilities': facilities, 'sr_open': sr_open,
    })


@require_access('can_manage_assets')
def facility_create(request):
    form = FacilityForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Facility created.')
        return redirect('facility_list')
    return render(request, 'maintenance/facility_form.html', {'form': form, 'title': 'Add Facility'})


@require_access('can_manage_assets')
def facility_edit(request, pk):
    facility = get_object_or_404(Facility, pk=pk)
    form = FacilityForm(request.POST or None, instance=facility)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Facility updated.')
        return redirect('facility_list')
    return render(request, 'maintenance/facility_form.html', {'form': form, 'title': 'Edit Facility'})


@require_access('can_manage_assets')
def facility_delete(request, pk):
    facility = get_object_or_404(Facility, pk=pk)
    if request.method == 'POST':
        facility.delete()
        messages.success(request, 'Facility deleted.')
        return redirect('facility_list')
    return render(request, 'maintenance/confirm_delete.html', {'obj': facility, 'type': 'Facility'})


@require_access('can_access_assets')
def service_request_list(request):
    srs = FacilityServiceRequest.objects.select_related('facility').all()
    status_filter = request.GET.get('status', '')
    if status_filter:
        srs = srs.filter(status=status_filter)
    return render(request, 'maintenance/sr_list.html', {
        'srs': srs, 'selected_status': status_filter, 'today': date.today(),
    })


@require_access('can_create_wr')
def service_request_create(request):
    form = FacilityServiceRequestForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        sr = form.save(commit=False)
        sr.created_by = request.user
        sr.save()
        messages.success(request, f'Service Request {sr.sr_number} submitted.')
        return redirect('service_request_list')
    return render(request, 'maintenance/sr_form.html', {'form': form, 'title': 'New Service Request'})


@require_access('can_create_wr')
def service_request_edit(request, pk):
    sr = get_object_or_404(FacilityServiceRequest, pk=pk)
    form = FacilityServiceRequestForm(request.POST or None, instance=sr)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Service Request updated.')
        return redirect('service_request_list')
    return render(request, 'maintenance/sr_form.html', {'form': form, 'title': 'Edit Service Request'})


@require_access('can_create_wr')
def service_request_delete(request, pk):
    sr = get_object_or_404(FacilityServiceRequest, pk=pk)
    if request.method == 'POST':
        sr.delete()
        messages.success(request, 'Service Request deleted.')
        return redirect('service_request_list')
    return render(request, 'maintenance/confirm_delete.html', {'obj': sr, 'type': 'Service Request'})


# ══════════════════════════════════════════════════════════════════════════
# ISO VIEWS
# ══════════════════════════════════════════════════════════════════════════

# ── ISO DASHBOARD ──────────────────────────────────────────────────────────

@login_required
def iso_dashboard(request):
    from datetime import date, timedelta
    today = date.today()
    soon  = today + timedelta(days=30)
    ctx = {
        # Calibration
        'cal_overdue':   Instrument.objects.filter(next_calibration__lt=today, status='Active').count(),
        'cal_due_soon':  Instrument.objects.filter(next_calibration__gte=today, next_calibration__lte=soon).count(),
        'cal_total':     Instrument.objects.count(),
        # NCR
        'ncr_open':      NonConformance.objects.filter(status__in=['Open','Under Analysis','Action Planned','In Progress']).count(),
        'ncr_overdue':   NonConformance.objects.filter(target_date__lt=today, status__in=['Open','Under Analysis','Action Planned','In Progress']).count(),
        'ncr_major':     NonConformance.objects.filter(grade='Major', status__in=['Open','Under Analysis','Action Planned','In Progress']).count(),
        # Documents
        'doc_approved':  ISODocument.objects.filter(status='Approved').count(),
        'doc_review_due':ISODocument.objects.filter(review_date__lte=today, status='Approved').count(),
        'doc_total':     ISODocument.objects.count(),
        # Audits
        'aud_planned':   InternalAudit.objects.filter(status='Planned').count(),
        'aud_completed': InternalAudit.objects.filter(status='Completed').count(),
        # Environmental
        'env_significant': EnvironmentalAspect.objects.filter(significance='Significant').count(),
        'env_total':       EnvironmentalAspect.objects.count(),
        # Recent
        'recent_ncrs':   NonConformance.objects.select_related().order_by('-created_at')[:5],
        'overdue_cals':  Instrument.objects.filter(next_calibration__lt=today, status='Active').order_by('next_calibration')[:5],
        'upcoming_audits': InternalAudit.objects.filter(status='Planned').order_by('planned_date')[:5],
        'today': today,
    }
    return render(request, 'maintenance/iso_dashboard.html', ctx)


# ── CALIBRATION ────────────────────────────────────────────────────────────

@login_required
def instrument_list(request):
    from datetime import date, timedelta
    today   = date.today()
    soon    = today + timedelta(days=30)
    status  = request.GET.get('status', '')
    instruments = Instrument.objects.select_related('asset').all()
    if status == 'overdue':
        instruments = instruments.filter(next_calibration__lt=today, status='Active')
    elif status == 'due_soon':
        instruments = instruments.filter(next_calibration__gte=today, next_calibration__lte=soon)
    elif status:
        instruments = instruments.filter(status=status)
    return render(request, 'maintenance/instrument_list.html', {
        'instruments': instruments, 'today': today, 'soon': soon,
        'selected_status': status,
    })


@login_required
def instrument_detail(request, pk):
    instrument = get_object_or_404(Instrument, pk=pk)
    records    = instrument.calibration_records.all()[:10]
    return render(request, 'maintenance/instrument_detail.html', {
        'instrument': instrument, 'records': records
    })


@login_required
def instrument_create(request):
    form = InstrumentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Instrument added to calibration register.')
        return redirect('instrument_list')
    return render(request, 'maintenance/instrument_form.html', {'form': form, 'title': 'Add Instrument'})


@login_required
def instrument_edit(request, pk):
    instrument = get_object_or_404(Instrument, pk=pk)
    form = InstrumentForm(request.POST or None, instance=instrument)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Instrument updated.')
        return redirect('instrument_detail', pk=pk)
    return render(request, 'maintenance/instrument_form.html', {'form': form, 'title': 'Edit Instrument'})


@login_required
def instrument_delete(request, pk):
    instrument = get_object_or_404(Instrument, pk=pk)
    if request.method == 'POST':
        instrument.delete()
        messages.success(request, 'Instrument deleted.')
        return redirect('instrument_list')
    return render(request, 'maintenance/confirm_delete.html', {'obj': instrument, 'type': 'Instrument'})


@login_required
def calibration_add(request, instrument_pk):
    instrument = get_object_or_404(Instrument, pk=instrument_pk)
    initial    = {'instrument': instrument}
    form = CalibrationRecordForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        record = form.save(commit=False)
        record.created_by = request.user
        record.save()
        # Update instrument dates and status
        instrument.last_calibration = record.calibration_date
        instrument.next_calibration = record.next_due
        instrument.status = 'Active' if record.result in ['Pass','Pass with Note','Adjusted'] else 'Out of Service'
        instrument.save()
        messages.success(request, f'Calibration record added. Next due: {record.next_due}')
        return redirect('instrument_detail', pk=instrument_pk)
    return render(request, 'maintenance/calibration_form.html', {
        'form': form, 'instrument': instrument, 'title': f'Add Calibration — {instrument.name}'
    })


# ── NCR & CORRECTIVE ACTIONS ───────────────────────────────────────────────

@login_required
def ncr_list(request):
    ncrs = NonConformance.objects.all()
    status   = request.GET.get('status', '')
    grade    = request.GET.get('grade', '')
    standard = request.GET.get('standard', '')
    if status:   ncrs = ncrs.filter(status=status)
    if grade:    ncrs = ncrs.filter(grade=grade)
    if standard: ncrs = ncrs.filter(iso_standard=standard)
    return render(request, 'maintenance/ncr_list.html', {
        'ncrs': ncrs, 'today': date.today(),
        'selected_status': status, 'selected_grade': grade, 'selected_standard': standard,
    })


@login_required
def ncr_detail(request, pk):
    ncr = get_object_or_404(NonConformance, pk=pk)
    return render(request, 'maintenance/ncr_detail.html', {'ncr': ncr})


@login_required
def ncr_create(request):
    form = NonConformanceForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        ncr = form.save(commit=False)
        ncr.created_by = request.user
        ncr.save()
        messages.success(request, f'NCR {ncr.ncr_number} created.')
        return redirect('ncr_detail', pk=ncr.pk)
    return render(request, 'maintenance/ncr_form.html', {'form': form, 'title': 'New Non-Conformance'})


@login_required
def ncr_edit(request, pk):
    ncr  = get_object_or_404(NonConformance, pk=pk)
    form = NonConformanceForm(request.POST or None, instance=ncr)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'NCR updated.')
        return redirect('ncr_detail', pk=pk)
    return render(request, 'maintenance/ncr_form.html', {'form': form, 'title': f'Edit {ncr.ncr_number}'})


@login_required
def ncr_delete(request, pk):
    ncr = get_object_or_404(NonConformance, pk=pk)
    if request.method == 'POST':
        ncr.delete()
        messages.success(request, 'NCR deleted.')
        return redirect('ncr_list')
    return render(request, 'maintenance/confirm_delete.html', {'obj': ncr, 'type': 'NCR'})


# ── ISO DOCUMENTS ──────────────────────────────────────────────────────────

@login_required
def iso_doc_list(request):
    docs     = ISODocument.objects.all()
    standard = request.GET.get('standard', '')
    status   = request.GET.get('status', '')
    doc_type = request.GET.get('doc_type', '')
    if standard: docs = docs.filter(iso_standard=standard)
    if status:   docs = docs.filter(status=status)
    if doc_type: docs = docs.filter(doc_type=doc_type)
    return render(request, 'maintenance/iso_doc_list.html', {
        'docs': docs, 'today': date.today(),
        'selected_standard': standard, 'selected_status': status, 'selected_type': doc_type,
    })


@login_required
def iso_doc_create(request):
    form = ISODocumentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        doc = form.save(commit=False)
        doc.created_by = request.user
        doc.save()
        messages.success(request, f'Document {doc.doc_number} created.')
        return redirect('iso_doc_list')
    return render(request, 'maintenance/iso_doc_form.html', {'form': form, 'title': 'Add ISO Document'})


@login_required
def iso_doc_edit(request, pk):
    doc  = get_object_or_404(ISODocument, pk=pk)
    form = ISODocumentForm(request.POST or None, instance=doc)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Document updated.')
        return redirect('iso_doc_list')
    return render(request, 'maintenance/iso_doc_form.html', {'form': form, 'title': f'Edit {doc.doc_number}'})


@login_required
def iso_doc_delete(request, pk):
    doc = get_object_or_404(ISODocument, pk=pk)
    if request.method == 'POST':
        doc.delete()
        messages.success(request, 'Document deleted.')
        return redirect('iso_doc_list')
    return render(request, 'maintenance/confirm_delete.html', {'obj': doc, 'type': 'ISO Document'})


# ── INTERNAL AUDITS ────────────────────────────────────────────────────────

@login_required
def audit_list(request):
    audits = InternalAudit.objects.all()
    return render(request, 'maintenance/audit_list.html', {'audits': audits})


@login_required
def audit_detail(request, pk):
    audit = get_object_or_404(InternalAudit, pk=pk)
    ncrs  = NonConformance.objects.filter(source='Internal Audit').order_by('-created_at')[:10]
    return render(request, 'maintenance/audit_detail.html', {'audit': audit, 'ncrs': ncrs})


@login_required
def audit_create(request):
    form = InternalAuditForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        audit = form.save(commit=False)
        audit.created_by = request.user
        audit.save()
        messages.success(request, f'Audit {audit.audit_number} scheduled.')
        return redirect('audit_detail', pk=audit.pk)
    return render(request, 'maintenance/audit_form.html', {'form': form, 'title': 'Schedule Internal Audit'})


@login_required
def audit_edit(request, pk):
    audit = get_object_or_404(InternalAudit, pk=pk)
    form  = InternalAuditForm(request.POST or None, instance=audit)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Audit updated.')
        return redirect('audit_detail', pk=pk)
    return render(request, 'maintenance/audit_form.html', {'form': form, 'title': f'Edit {audit.audit_number}'})


@login_required
def audit_delete(request, pk):
    audit = get_object_or_404(InternalAudit, pk=pk)
    if request.method == 'POST':
        audit.delete()
        messages.success(request, 'Audit deleted.')
        return redirect('audit_list')
    return render(request, 'maintenance/confirm_delete.html', {'obj': audit, 'type': 'Internal Audit'})


# ── ENVIRONMENTAL ASPECTS ──────────────────────────────────────────────────

@login_required
def env_list(request):
    aspects = EnvironmentalAspect.objects.select_related('asset').all()
    sig     = request.GET.get('significance', '')
    if sig: aspects = aspects.filter(significance=sig)
    sig_count   = EnvironmentalAspect.objects.filter(significance='Significant').count()
    nonsig_count = EnvironmentalAspect.objects.filter(significance='Non-Significant').count()
    return render(request, 'maintenance/env_list.html', {
        'aspects': aspects, 'selected_sig': sig,
        'sig_count': sig_count, 'nonsig_count': nonsig_count,
    })


@login_required
def env_create(request):
    form = EnvironmentalAspectForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        asp = form.save(commit=False)
        asp.created_by = request.user
        asp.save()
        messages.success(request, f'Environmental aspect {asp.aspect_number} added.')
        return redirect('env_list')
    return render(request, 'maintenance/env_form.html', {'form': form, 'title': 'Add Environmental Aspect'})


@login_required
def env_edit(request, pk):
    aspect = get_object_or_404(EnvironmentalAspect, pk=pk)
    form   = EnvironmentalAspectForm(request.POST or None, instance=aspect)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Aspect updated.')
        return redirect('env_list')
    return render(request, 'maintenance/env_form.html', {'form': form, 'title': 'Edit Environmental Aspect'})


@login_required
def env_delete(request, pk):
    aspect = get_object_or_404(EnvironmentalAspect, pk=pk)
    if request.method == 'POST':
        aspect.delete()
        messages.success(request, 'Aspect deleted.')
        return redirect('env_list')
    return render(request, 'maintenance/confirm_delete.html', {'obj': aspect, 'type': 'Environmental Aspect'})


# ══════════════════════════════════════════════════════════════════════════
# SAFETY PERMIT MODULE (Permit to Work)
# ══════════════════════════════════════════════════════════════════════════

@require_access('can_access_safety')
def safety_permit_list(request):
    permits = SafetyPermit.objects.select_related('work_order').all()
    status   = request.GET.get('status', '')
    risk     = request.GET.get('risk', '')
    if status: permits = permits.filter(status=status)
    if risk:   permits = permits.filter(risk_level=risk)
    pending_count = SafetyPermit.objects.filter(status='Pending').count()
    active_count  = SafetyPermit.objects.filter(status='Active').count()
    return render(request, 'maintenance/safety_list.html', {
        'permits': permits, 'selected_status': status, 'selected_risk': risk,
        'pending_count': pending_count, 'active_count': active_count,
    })


@require_access('can_access_safety')
def safety_permit_detail(request, pk):
    permit = get_object_or_404(SafetyPermit, pk=pk)
    return render(request, 'maintenance/safety_detail.html', {'permit': permit})


@require_access('can_access_safety')
def safety_permit_create(request, wo_pk=None):
    initial = {}
    wo = None
    if wo_pk:
        wo = get_object_or_404(WorkOrder, pk=wo_pk)
        initial = {
            'work_order': wo,
            'work_description': wo.description or wo.title,
            'location': wo.asset.location if wo.asset else '',
            'requested_by': wo.assigned_to,
        }
    form = SafetyPermitForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        permit = form.save(commit=False)
        permit.created_by = request.user
        permit.save()
        notif_service.notify_safety_permit_created(permit, created_by=request.user)
        messages.success(request, f'🦺 Safety Permit {permit.permit_number} created — pending approval.')
        return redirect('safety_permit_detail', pk=permit.pk)
    return render(request, 'maintenance/safety_form.html', {
        'form': form, 'title': 'New Safety Permit (Permit to Work)', 'wo': wo
    })


@require_access('can_access_safety')
def safety_permit_edit(request, pk):
    permit = get_object_or_404(SafetyPermit, pk=pk)
    form = SafetyPermitForm(request.POST or None, instance=permit)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Safety Permit updated.')
        return redirect('safety_permit_detail', pk=pk)
    return render(request, 'maintenance/safety_form.html', {
        'form': form, 'title': f'Edit {permit.permit_number}', 'wo': permit.work_order
    })


@require_access('can_approve_safety')
def safety_permit_approve(request, pk):
    permit = get_object_or_404(SafetyPermit, pk=pk)
    form = SafetyPermitApprovalForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        decision = form.cleaned_data['decision']
        permit.status = decision
        permit.approved_by = form.cleaned_data['approved_by']
        permit.approval_notes = form.cleaned_data.get('approval_notes', '')
        permit.rejection_reason = form.cleaned_data.get('rejection_reason', '')
        permit.approved_at = timezone.now()
        permit.save()
        if decision == 'Approved':
            messages.success(request, f'✅ Permit {permit.permit_number} approved. Work may begin.')
        else:
            messages.warning(request, f'❌ Permit {permit.permit_number} rejected.')
        return redirect('safety_permit_detail', pk=pk)
    return render(request, 'maintenance/safety_approve.html', {'form': form, 'permit': permit})


@require_access('can_access_safety')
def safety_permit_close(request, pk):
    permit = get_object_or_404(SafetyPermit, pk=pk)
    form = SafetyPermitCloseForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        permit.status = 'Closed'
        permit.closed_by = form.cleaned_data['closed_by']
        permit.closure_notes = form.cleaned_data.get('closure_notes', '')
        permit.closed_at = timezone.now()
        permit.save()
        messages.success(request, f'Permit {permit.permit_number} closed. Work area cleared.')
        return redirect('safety_permit_detail', pk=pk)
    return render(request, 'maintenance/safety_close.html', {'form': form, 'permit': permit})


@require_access('can_access_safety')
def safety_permit_activate(request, pk):
    """Mark an approved permit as Active (work physically started)."""
    permit = get_object_or_404(SafetyPermit, pk=pk)
    if request.method == 'POST' and permit.status == 'Approved':
        permit.status = 'Active'
        permit.save()
        messages.success(request, f'Permit {permit.permit_number} is now Active.')
    return redirect('safety_permit_detail', pk=pk)


@require_access('can_access_safety')
def safety_permit_delete(request, pk):
    permit = get_object_or_404(SafetyPermit, pk=pk)
    if request.method == 'POST':
        permit.delete()
        messages.success(request, 'Safety permit deleted.')
        return redirect('safety_permit_list')
    return render(request, 'maintenance/confirm_delete.html', {'obj': permit, 'type': 'Safety Permit'})
