from django import template
register = template.Library()

@register.filter
def getitem(form, field_name):
    """Return form field by name: {{ form|getitem:'field_name' }}"""
    try:
        return form[field_name]
    except Exception:
        return ''

@register.filter
def split(value, sep=' '):
    return value.split(sep)
