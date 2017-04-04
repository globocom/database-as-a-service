from django import template
from django.conf import settings

register = template.Library()


@register.assignment_tag()
def setting(var_name):
    """
        Get a var from settings
    """
    return getattr(settings, var_name)
