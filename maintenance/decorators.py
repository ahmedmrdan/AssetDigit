"""
Custom decorators for page-level access control.
Shows a full ACCESS DENIED page instead of silent redirect.
"""
from functools import wraps
from django.shortcuts import render, redirect


def require_access(permission_field):
    """
    Shows a full access-denied page if user lacks the permission.
    Admin (is_staff) users always pass.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.is_staff:
                return view_func(request, *args, **kwargs)
            try:
                profile = request.user.profile
                if not profile.is_active:
                    return render(request, 'maintenance/access_denied.html', {
                        'reason': 'deactivated',
                        'message_en': 'Your account has been deactivated. Please contact the administrator.',
                        'message_ar': 'تم تعطيل حسابك. يرجى التواصل مع المسؤول.',
                    }, status=403)
                if getattr(profile, permission_field, False):
                    return view_func(request, *args, **kwargs)
                else:
                    # Map permission field to page name
                    page_names = {
                        'can_access_dashboard':   {'en': 'Dashboard',      'ar': 'لوحة التحكم'},
                        'can_access_assets':      {'en': 'Assets',         'ar': 'الأصول والمعدات'},
                        'can_access_workrequest': {'en': 'Work Requests',  'ar': 'طلبات العمل'},
                        'can_access_workorder':   {'en': 'Work Orders',    'ar': 'أوامر العمل'},
                        'can_access_pm':          {'en': 'PM Schedule',    'ar': 'جدول الصيانة الوقائية'},
                        'can_access_reports':     {'en': 'Reports',        'ar': 'التقارير'},
                        'can_create_wr':          {'en': 'Create Work Requests', 'ar': 'إنشاء طلبات العمل'},
                        'can_convert_wr':         {'en': 'Convert Work Requests', 'ar': 'تحويل طلبات العمل'},
                        'can_create_wo':          {'en': 'Create Work Orders', 'ar': 'إنشاء أوامر العمل'},
                        'can_close_wo':           {'en': 'Close Work Orders', 'ar': 'إغلاق أوامر العمل'},
                        'can_manage_assets':      {'en': 'Manage Assets',  'ar': 'إدارة الأصول'},
                        'can_manage_pm':          {'en': 'Manage PM Tasks', 'ar': 'إدارة مهام الصيانة'},
                    }
                    page = page_names.get(permission_field, {'en': 'this page', 'ar': 'هذه الصفحة'})
                    return render(request, 'maintenance/access_denied.html', {
                        'reason': 'no_permission',
                        'page_en': page['en'],
                        'page_ar': page['ar'],
                        'message_en': f'You do not have permission to access "{page["en"]}".',
                        'message_ar': f'ليس لديك صلاحية للوصول إلى "{page["ar"]}".',
                        'user_role': getattr(profile, 'get_role_display', lambda: profile.role)(),
                    }, status=403)
            except Exception:
                return render(request, 'maintenance/access_denied.html', {
                    'reason': 'no_profile',
                    'message_en': 'Access denied. Your user profile is not configured. Contact the administrator.',
                    'message_ar': 'تم رفض الوصول. لم يتم تكوين ملف تعريف المستخدم. تواصل مع المسؤول.',
                }, status=403)
        return wrapper
    return decorator


def admin_only(view_func):
    """Only admin (is_staff) users can access. Shows full denied page to others."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.is_staff:
            return view_func(request, *args, **kwargs)
        return render(request, 'maintenance/access_denied.html', {
            'reason': 'admin_only',
            'message_en': 'This page is for administrators only.',
            'message_ar': 'هذه الصفحة للمسؤولين فقط.',
        }, status=403)
    return wrapper
