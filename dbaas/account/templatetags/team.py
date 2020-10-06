# -*- coding:utf-8 -*-
from django import template
from django.utils.html import format_html
import logging
from django.db.models.loading import get_model
from django.core.urlresolvers import reverse

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

    envs = team.environments_in_use_for()
    html.append("<ul>")
    for environment in environments:
        count = 0
        for env in envs:
            if (env == environment.id):
                count = count + 1
        html.append("<li>%s: %d of %s in use</li>" % (
            environment,
            count,
            team.database_alocation_limit)
        )

    return format_html("".join(html))


@register.simple_tag
def model_view_url(app_label, app_name, model_name):
    model = get_model(app_label, model_name)
    url_name = 'admin:{}_{}_changelist'.format(
        app_label, model._meta.model_name
    )
    return reverse(url_name, current_app=app_name)
