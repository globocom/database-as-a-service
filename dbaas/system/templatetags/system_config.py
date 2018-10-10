# -*- coding:utf-8 -*-
from django import template
from system.models import Configuration

register = template.Library()


@register.simple_tag(takes_context=True)
def get_configuration(context, configuration_name, context_var_name):
    """
    Usage: {% get_configuration config_name context_var %}

    Search config name on system configuration and set context_var on
    page context
    """
    config_val = Configuration.get_by_name(configuration_name) or ''

    context[context_var_name] = config_val

    return ''
