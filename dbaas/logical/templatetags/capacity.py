# -*- coding:utf-8 -*-
from util.html import render_progress_bar
from django import template
import logging

register = template.Library()

MB_FACTOR = 1.0 / 1024.0 / 1024.0
LOG = logging.getLogger(__name__)


@register.simple_tag
def render_capacity_html(database):
    try:
        message = "%d of %s (MB)" % (database.used_size * MB_FACTOR, (database.total_size * MB_FACTOR) or 'unlimited')
        return render_progress_bar(database.capacity*100, message=message)
    except:
        # any error show Unkown message and log error. This avoid break page if there is a problem
        # with some database
        LOG.exception('Error getting capacity of database %s', database)
        return "Unkown"
