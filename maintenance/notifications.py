"""
Notification helpers — called from views whenever a key event happens.
Each function creates Notification records for the right users based on their preferences.
"""
from django.contrib.auth.models import User
from .models import Notification, UserProfile


def _send(recipient, notif_type, title, message, link='', priority='normal',
          work_request=None, work_order=None):
    """Create one notification record for one user."""
    Notification.objects.create(
        recipient=recipient,
        notif_type=notif_type,
        priority=priority,
        title=title,
        message=message,
        link=link,
        work_request=work_request,
        work_order=work_order,
    )


def _users_with_pref(pref_field):
    """Return all active users who have a notification preference enabled."""
    profiles = UserProfile.objects.filter(
        is_active=True,
        **{pref_field: True}
    ).select_related('user')
    return [p.user for p in profiles]


# ── WORK REQUEST EVENTS ────────────────────────────────────────────────────

def notify_wr_created(wr, created_by):
    """
    When operator submits a WR:
    → Notify all users with notify_wr_new = True
      (typically: section heads, engineers, maintenance team)
    """
    recipients = _users_with_pref('notify_wr_new')
    priority   = 'critical' if wr.priority in ['Critical', 'High'] else 'normal'
    link       = f'/workrequests/{wr.pk}/'

    for user in recipients:
        if user == created_by:
            continue  # don't notify the person who created it
        _send(
            recipient    = user,
            notif_type   = 'wr_new',
            priority     = priority,
            title        = f'🚨 New Work Request: {wr.wr_number}',
            message      = (f'Machine: {wr.asset.name if wr.asset else "N/A"}\n'
                            f'Alarm: {wr.alarm_type} {("— Code: " + wr.alarm_code) if wr.alarm_code else ""}\n'
                            f'Priority: {wr.priority}\n'
                            f'Reported by: {wr.reported_by} ({wr.reporter_department})\n'
                            f'Problem: {wr.description[:200]}'),
            link         = link,
            work_request = wr,
        )


def notify_wr_converted(wr, wo, converted_by):
    """
    When maintenance converts WR → WO:
    → Notify the original reporter's team (users with notify_wr_converted)
      i.e. production operators get told their request was accepted
    → Also notify assigned technician
    """
    link_wr = f'/workrequests/{wr.pk}/'
    link_wo = f'/workorders/{wo.pk}/'

    # Notify everyone subscribed to this event
    for user in _users_with_pref('notify_wr_converted'):
        if user == converted_by:
            continue
        _send(
            recipient    = user,
            notif_type   = 'wr_converted',
            priority     = 'normal',
            title        = f'✅ Work Request {wr.wr_number} → Work Order {wo.wo_number}',
            message      = (f'Your work request has been reviewed and converted.\n'
                            f'Machine: {wr.asset.name if wr.asset else "N/A"}\n'
                            f'Assigned to: {wo.assigned_to}\n'
                            f'Due date: {wo.due_date.strftime("%d/%m/%Y") if wo.due_date else "TBD"}\n'
                            f'Work Order: {wo.wo_number}'),
            link         = link_wo,
            work_request = wr,
            work_order   = wo,
        )

    # Notify the assigned technician specifically (by name match on username/full_name)
    if wo.assigned_to:
        assigned = (User.objects.filter(username__iexact=wo.assigned_to).first() or
                    User.objects.filter(first_name__iexact=wo.assigned_to.split()[0]).first())
        if assigned and assigned != converted_by:
            _send(
                recipient   = assigned,
                notif_type  = 'wo_assigned',
                priority    = 'high',
                title       = f'📋 Work Order {wo.wo_number} Assigned to You',
                message     = (f'You have been assigned a new work order.\n'
                               f'Machine: {wo.asset.name if wo.asset else "N/A"}\n'
                               f'Type: {wo.wo_type} — Priority: {wo.priority}\n'
                               f'Due: {wo.due_date.strftime("%d/%m/%Y") if wo.due_date else "TBD"}\n'
                               f'Description: {wo.description[:150]}'),
                link        = link_wo,
                work_order  = wo,
            )


def notify_wr_rejected(wr, rejected_by):
    """
    When a WR is rejected:
    → Notify users subscribed to notify_wr_rejected
      (usually the operator/reporter's team)
    """
    link = f'/workrequests/{wr.pk}/'
    for user in _users_with_pref('notify_wr_rejected'):
        if user == rejected_by:
            continue
        _send(
            recipient    = user,
            notif_type   = 'wr_rejected',
            priority     = 'normal',
            title        = f'❌ Work Request {wr.wr_number} Rejected',
            message      = (f'Work Request has been reviewed and rejected.\n'
                            f'Machine: {wr.asset.name if wr.asset else "N/A"}\n'
                            f'Review Notes: {wr.review_notes or "No notes provided"}\n'
                            f'Reviewed by: {rejected_by.get_full_name() or rejected_by.username}'),
            link         = link,
            work_request = wr,
        )


# ── SAFETY PERMIT EVENTS ───────────────────────────────────────────────────

def notify_safety_permit_created(permit, created_by):
    """
    When a new Safety Permit is created (manually or auto on WO creation):
    → Notify users with notify_safety_permit = True (safety officers/approvers)
    """
    link = f'/safety/{permit.pk}/'
    for user in _users_with_pref('notify_safety_permit'):
        if user == created_by:
            continue
        _send(
            recipient   = user,
            notif_type  = 'wo_assigned',  # reuse generic type for now
            priority    = 'critical' if permit.risk_level in ['High', 'Critical'] else 'high',
            title       = f'🦺 New Safety Permit Pending Approval: {permit.permit_number}',
            message     = (f'Permit Type: {permit.get_permit_type_display()}\n'
                           f'Risk Level: {permit.risk_level}\n'
                           f'Work Order: {permit.work_order.wo_number}\n'
                           f'Location: {permit.location or (permit.work_order.asset.location if permit.work_order.asset else "N/A")}\n'
                           f'Requested by: {permit.requested_by}\n'
                           f'Work: {permit.work_description[:150]}'),
            link        = link,
            work_order  = permit.work_order,
        )


# ── WORK ORDER EVENTS ──────────────────────────────────────────────────────

def notify_wo_completed(wo, completed_by):
    """
    When a WO is marked Completed:
    → Notify users with notify_wo_completed
      (usually production team — so they know the machine is fixed)
    """
    link = f'/workorders/{wo.pk}/'
    for user in _users_with_pref('notify_wo_completed'):
        if user == completed_by:
            continue
        _send(
            recipient   = user,
            notif_type  = 'wo_completed',
            priority    = 'normal',
            title       = f'✅ Work Order {wo.wo_number} Completed',
            message     = (f'Maintenance work has been completed.\n'
                           f'Machine: {wo.asset.name if wo.asset else "N/A"}\n'
                           f'Completed by: {completed_by.get_full_name() or completed_by.username}\n'
                           f'Actual hours: {wo.actual_hours or "N/A"}\n'
                           f'The equipment should now be operational.'),
            link        = link,
            work_order  = wo,
        )

