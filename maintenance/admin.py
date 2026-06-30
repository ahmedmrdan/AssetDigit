from django.contrib import admin
from .models import Asset, WorkOrder, PMSchedule, SparePartUsage, WorkRequest, UserProfile, Notification, CompanySettings, SafetyPermit


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ['asset_id', 'name', 'category', 'location', 'status', 'last_pm_date']
    list_filter  = ['category', 'status']
    search_fields = ['asset_id', 'name', 'location']


class SparePartInline(admin.TabularInline):
    model = SparePartUsage
    extra = 1


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ['wo_number', 'title', 'asset', 'priority', 'status', 'assigned_to', 'due_date']
    list_filter  = ['priority', 'status', 'wo_type']
    search_fields = ['wo_number', 'title', 'assigned_to']
    inlines = [SparePartInline]


@admin.register(PMSchedule)
class PMScheduleAdmin(admin.ModelAdmin):
    list_display = ['task_name', 'asset', 'frequency', 'next_due', 'assigned_to', 'status']
    list_filter  = ['frequency', 'status']
    search_fields = ['task_name', 'assigned_to']


@admin.register(WorkRequest)
class WorkRequestAdmin(admin.ModelAdmin):
    list_display  = ['wr_number', 'title', 'asset', 'alarm_type', 'priority', 'status', 'reported_by', 'breakdown_time']
    list_filter   = ['priority', 'status', 'alarm_type', 'breakdown_type']
    search_fields = ['wr_number', 'title', 'reported_by', 'alarm_code']
    readonly_fields = ['wr_number', 'converted_to_wo', 'reviewed_by', 'reviewed_at']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display  = ['user', 'role', 'department', 'is_active']
    list_filter   = ['role', 'is_active']
    search_fields = ['user__username', 'user__first_name', 'department']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = ['recipient', 'notif_type', 'title', 'priority', 'is_read', 'created_at']
    list_filter   = ['notif_type', 'priority', 'is_read']
    search_fields = ['recipient__username', 'title']
    readonly_fields = ['created_at']


@admin.register(CompanySettings)
class CompanySettingsAdmin(admin.ModelAdmin):
    list_display = ['factory_name', 'location', 'phone', 'updated_at']


@admin.register(SafetyPermit)
class SafetyPermitAdmin(admin.ModelAdmin):
    list_display  = ['permit_number', 'work_order', 'permit_type', 'risk_level', 'status', 'requested_by', 'created_at']
    list_filter   = ['status', 'permit_type', 'risk_level']
    search_fields = ['permit_number', 'requested_by', 'work_order__wo_number']
