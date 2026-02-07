import json
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def to_json(value):
    """Convert a Python object to JSON string for use in JavaScript."""
    return mark_safe(json.dumps(value))
