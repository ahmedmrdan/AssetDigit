from .models import CompanySettings


def company_settings(request):
    """Inject CompanySettings into every template context."""
    try:
        settings_obj = CompanySettings.get()
    except Exception:
        settings_obj = None
    return {'company': settings_obj}
