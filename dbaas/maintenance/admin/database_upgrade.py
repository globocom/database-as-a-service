# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from django.core.urlresolvers import reverse
from django.contrib import admin
from django.utils.html import format_html
from ..models import DatabaseUpgrade


LOG = logging.getLogger(__name__)


class DatabaseUpgradeAdmin(admin.ModelAdmin):
    search_fields = ("database__name", "task__id", "task__task_id")
    list_filter = [
        "database__team", "source_plan", "target_plan", "source_plan__engine",
        "status",
    ]

    actions = None
    list_display = (
        "database", "database_team", "source_plan", "target_plan",
        "current_step", "friendly_status", "link_task", "started_at",
        "finished_at", "button_retry"
    )

    readonly_fields = (
        "database", "source_plan", "target_plan", "task", "started_at",
        "finished_at", "current_step", "status"
    )

    model = DatabaseUpgrade
    ordering = ["-started_at"]

    def friendly_status(self, upgrade):
        html_waiting = '<span class="label label-warning">Waiting</span>'
        html_running = '<span class="label label-success">Running</span>'
        html_error = '<span class="label label-important">Error</span>'
        html_success = '<span class="label label-info">Success</span>'

        if upgrade.status == DatabaseUpgrade.WAITING:
            return format_html(html_waiting)
        elif upgrade.status == DatabaseUpgrade.RUNNING:
            return format_html(html_running)
        elif upgrade.status == DatabaseUpgrade.ERROR:
            return format_html(html_error)
        elif upgrade.status == DatabaseUpgrade.SUCCESS:
            return format_html(html_success)
    friendly_status.short_description = "Status"

    def database_team(self, upgrade):
        return upgrade.database.team.name
    database_team.short_description = "Team"

    def link_task(self, upgrade):
        url = reverse(
            'admin:notification_taskhistory_change', args=[upgrade.task.id]
        )
        return format_html(
            "<a href={}>{}</a>".format(url, upgrade.task.id)
        )
    link_task.short_description = "Task"

    def button_retry(self, upgrade):
        if not upgrade.is_status_error:
            return 'N/A'


        url = upgrade.database.get_upgrade_retry_url()
        html = "<a class='btn btn-info' href='{}'>" \
               "<i class='icon-repeat icon-white'></i>" \
               "</a>".format(url)

        return format_html(html)
    button_retry.short_description = "Retry"

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False
