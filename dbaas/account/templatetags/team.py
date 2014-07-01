# -*- coding:utf-8 -*-
from django import template
from django.utils.html import format_html, escape
import logging

from physical.models import Environment

register = template.Library()

MB_FACTOR = 1.0 / 1024.0 / 1024.0
LOG = logging.getLogger(__name__)

def get_environments():
    return Environment.objects.all()

@register.simple_tag
def render_usage(team):
    environments = get_environments()
    html = []
    html.append("<ul>")
    for environment in environments:
        html.append("<li>%s: %s of %s in use</li>" % (environment,
                                                        team.count_databases_in_use(environment),
                                                        team.database_alocation_limit))

    return format_html("".join(html))

