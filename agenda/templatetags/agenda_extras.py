from django import template
from django.utils import timezone

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def get_event_top(value):
    """Calculates the top position in pixels for an event starting at 06:00 AM"""
    if not value:
        return 0
    try:
        # Convert to local time if needed
        if timezone.is_aware(value):
            value = timezone.localtime(value)

        # Get hour and minute
        hour = value.hour
        minutes = value.minute

        # Start time is 06:00 (as defined in views.py hours_list)
        start_hour = 6

        offset = ((hour - start_hour) * 60) + minutes
        return offset
    except AttributeError:
        # Fallback if value is something else
        return 0
