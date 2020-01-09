# -*- coding:utf-8 -*-
from django import template

register = template.Library()


@register.simple_tag(takes_context=False)
def status_color(status_code):
    status_map = {
        0: 'info',
        1: 'warning',
        2: 'success',
        3: 'error'
    }
    return status_map.get(status_code)
