from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Assets
    path('assets/', views.asset_list, name='asset_list'),
    path('assets/add/', views.asset_create, name='asset_create'),
    path('assets/<int:pk>/', views.asset_detail, name='asset_detail'),
    path('assets/<int:pk>/edit/', views.asset_edit, name='asset_edit'),
    path('assets/<int:pk>/delete/', views.asset_delete, name='asset_delete'),

    # Work Orders
    path('workorders/', views.wo_list, name='wo_list'),
    path('workorders/add/', views.wo_create, name='wo_create'),
    path('workorders/<int:pk>/', views.wo_detail, name='wo_detail'),
    path('workorders/<int:wo_pk>/safety-permit/new/', views.safety_permit_create, name='safety_permit_create_for_wo'),
    path('workorders/<int:pk>/edit/', views.wo_edit, name='wo_edit'),
    path('workorders/<int:pk>/delete/', views.wo_delete, name='wo_delete'),
    path('workorders/<int:pk>/status/', views.wo_update_status, name='wo_update_status'),

    # PM Schedule
    path('pm/', views.pm_list, name='pm_list'),
    path('pm/add/', views.pm_create, name='pm_create'),
    path('pm/<int:pk>/edit/', views.pm_edit, name='pm_edit'),
    path('pm/<int:pk>/complete/', views.pm_complete, name='pm_complete'),
    path('pm/<int:pk>/delete/', views.pm_delete, name='pm_delete'),

    # Work Requests
    path('workrequests/', views.wr_list, name='wr_list'),
    path('workrequests/add/', views.wr_create, name='wr_create'),
    path('workrequests/<int:pk>/', views.wr_detail, name='wr_detail'),
    path('workrequests/<int:pk>/edit/', views.wr_edit, name='wr_edit'),
    path('workrequests/<int:pk>/delete/', views.wr_delete, name='wr_delete'),
    path('workrequests/<int:pk>/status/', views.wr_update_status, name='wr_update_status'),
    path('workrequests/<int:pk>/convert/', views.wr_convert, name='wr_convert'),

    # Reports
    path('reports/', views.reports, name='reports'),

    # Notifications
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/read-all/', views.notification_mark_all_read, name='notification_mark_all_read'),
    path('notifications/<int:pk>/read/', views.notification_mark_read, name='notification_mark_read'),
    path('notifications/<int:pk>/delete/', views.notification_delete, name='notification_delete'),
    path('notifications/api/count/', views.notification_count_api, name='notification_count_api'),

    # ISO Dashboard
    path('iso/', views.iso_dashboard, name='iso_dashboard'),

    # Calibration Management
    path('iso/calibration/', views.instrument_list, name='instrument_list'),
    path('iso/calibration/add/', views.instrument_create, name='instrument_create'),
    path('iso/calibration/<int:pk>/', views.instrument_detail, name='instrument_detail'),
    path('iso/calibration/<int:pk>/edit/', views.instrument_edit, name='instrument_edit'),
    path('iso/calibration/<int:pk>/delete/', views.instrument_delete, name='instrument_delete'),
    path('iso/calibration/<int:instrument_pk>/record/', views.calibration_add, name='calibration_add'),

    # NCR & Corrective Actions
    path('iso/ncr/', views.ncr_list, name='ncr_list'),
    path('iso/ncr/add/', views.ncr_create, name='ncr_create'),
    path('iso/ncr/<int:pk>/', views.ncr_detail, name='ncr_detail'),
    path('iso/ncr/<int:pk>/edit/', views.ncr_edit, name='ncr_edit'),
    path('iso/ncr/<int:pk>/delete/', views.ncr_delete, name='ncr_delete'),

    # ISO Documents
    path('iso/documents/', views.iso_doc_list, name='iso_doc_list'),
    path('iso/documents/add/', views.iso_doc_create, name='iso_doc_create'),
    path('iso/documents/<int:pk>/edit/', views.iso_doc_edit, name='iso_doc_edit'),
    path('iso/documents/<int:pk>/delete/', views.iso_doc_delete, name='iso_doc_delete'),

    # Internal Audits
    path('iso/audits/', views.audit_list, name='audit_list'),
    path('iso/audits/add/', views.audit_create, name='audit_create'),
    path('iso/audits/<int:pk>/', views.audit_detail, name='audit_detail'),
    path('iso/audits/<int:pk>/edit/', views.audit_edit, name='audit_edit'),
    path('iso/audits/<int:pk>/delete/', views.audit_delete, name='audit_delete'),

    # Environmental Aspects
    path('iso/environment/', views.env_list, name='env_list'),
    path('iso/environment/add/', views.env_create, name='env_create'),
    path('iso/environment/<int:pk>/edit/', views.env_edit, name='env_edit'),
    path('iso/environment/<int:pk>/delete/', views.env_delete, name='env_delete'),

    # Predictive Maintenance
    path('predictive/', views.predictive_list, name='predictive_list'),
    path('predictive/add/', views.predictive_create, name='predictive_create'),
    path('predictive/<int:pk>/delete/', views.predictive_delete, name='predictive_delete'),

    # Proactive Maintenance
    path('proactive/', views.proactive_list, name='proactive_list'),
    path('proactive/add/', views.proactive_create, name='proactive_create'),
    path('proactive/<int:pk>/edit/', views.proactive_edit, name='proactive_edit'),
    path('proactive/<int:pk>/delete/', views.proactive_delete, name='proactive_delete'),

    # Breakdown Analysis
    path('bda/', views.bda_list, name='bda_list'),
    path('bda/add/', views.bda_create, name='bda_create'),
    path('bda/<int:pk>/', views.bda_detail, name='bda_detail'),
    path('bda/<int:pk>/edit/', views.bda_edit, name='bda_edit'),
    path('bda/<int:pk>/delete/', views.bda_delete, name='bda_delete'),

    # Facilities Management
    path('facilities/', views.facility_list, name='facility_list'),
    path('facilities/add/', views.facility_create, name='facility_create'),
    path('facilities/<int:pk>/edit/', views.facility_edit, name='facility_edit'),
    path('facilities/<int:pk>/delete/', views.facility_delete, name='facility_delete'),
    path('facilities/service-requests/', views.service_request_list, name='service_request_list'),
    path('facilities/service-requests/add/', views.service_request_create, name='service_request_create'),
    path('facilities/service-requests/<int:pk>/edit/', views.service_request_edit, name='service_request_edit'),
    path('facilities/service-requests/<int:pk>/delete/', views.service_request_delete, name='service_request_delete'),

    # Safety Permits (Permit to Work)
    path('safety/', views.safety_permit_list, name='safety_permit_list'),
    path('safety/add/', views.safety_permit_create, name='safety_permit_create'),
    path('safety/<int:pk>/', views.safety_permit_detail, name='safety_permit_detail'),
    path('safety/<int:pk>/edit/', views.safety_permit_edit, name='safety_permit_edit'),
    path('safety/<int:pk>/approve/', views.safety_permit_approve, name='safety_permit_approve'),
    path('safety/<int:pk>/activate/', views.safety_permit_activate, name='safety_permit_activate'),
    path('safety/<int:pk>/close/', views.safety_permit_close, name='safety_permit_close'),
    path('safety/<int:pk>/delete/', views.safety_permit_delete, name='safety_permit_delete'),

    # Backup & Restore (Admin Only)
    path('backup/', views.backup_page, name='backup_page'),
    path('backup/download/', views.backup_download, name='backup_download'),
    path('backup/export-json/', views.backup_export_json, name='backup_export_json'),
    path('backup/export-excel/', views.backup_export_excel, name='backup_export_excel'),

    # Company Settings (Admin Only)
    path('settings/', views.company_settings_view, name='company_settings'),

    # User Management (Admin Only)
    path('users/', views.user_list, name='user_list'),
    path('users/add/', views.user_create, name='user_create'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),
    path('users/<int:pk>/toggle/', views.user_toggle_active, name='user_toggle_active'),
    path('users/<int:pk>/apply-role/', views.user_apply_role, name='user_apply_role'),
]
