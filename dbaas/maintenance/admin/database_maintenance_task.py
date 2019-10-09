# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.html import format_html
from ..models import DatabaseMaintenanceTask


class DatabaseMaintenanceTaskAdmin(admin.ModelAdmin):
    list_select_related = None
    search_fields = ("database__name", "task__id", "task__task_id")
    list_filter = [
        "database__team", "status",
    ]
    exclude = ("task", "can_do_retry")

    actions = None
    list_display = (
        "database", "database_team", "current_step", "friendly_status",
        "maintenance_action", "link_task", "started_at", "finished_at"
    )

    readonly_fields = (
        "database", "link_task", "started_at", "finished_at",
        "current_step", "status", "maintenance_action"
    )

    ordering = ["-started_at"]

    def friendly_status(self, maintenance_task):
        html_waiting = '<span class="label label-warning">Waiting</span>'
        html_running = '<span class="label label-success">Running</span>'
        html_error = '<span class="label label-important">Error</span>'
        html_success = '<span class="label label-info">Success</span>'
        html_rollback = '<span class="label label-info">Rollback</span>'

        html_status = ''
        if maintenance_task.status == DatabaseMaintenanceTask.WAITING:
            html_status = html_waiting
        elif maintenance_task.status == DatabaseMaintenanceTask.RUNNING:
            html_status = html_running
        elif maintenance_task.status == DatabaseMaintenanceTask.ERROR:
            html_status = html_error
        elif maintenance_task.status == DatabaseMaintenanceTask.SUCCESS:
            html_status = html_success
        elif maintenance_task.status == DatabaseMaintenanceTask.ROLLBACK:
            html_status = html_rollback

        return format_html(html_status)
    friendly_status.short_description = "Status"

    def database_team(self, maintenance_task):
        return maintenance_task.database.team.name
    database_team.short_description = "Team"

    def link_task(self, maintenance_task):
        url = reverse(
            'admin:notification_taskhistory_change',
            args=[maintenance_task.task.id]
        )
        return format_html(
            "<a href={}>{}</a>".format(url, maintenance_task.task.id)
        )
    link_task.short_description = "Task"

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def maintenance_action(self, maintenance_task):
        raise NotImplementedError()
    maintenance_action.short_description = "Action"
