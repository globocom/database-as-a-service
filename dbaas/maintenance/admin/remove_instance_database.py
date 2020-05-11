# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.html import format_html
from .database_maintenance_task import DatabaseMaintenanceTaskAdmin


class RemoveInstanceDatabaseAdmin(DatabaseMaintenanceTaskAdmin):

    list_filter = [
        "database__team", "current_step", "instance",
        "status",
    ]

    list_display = (
        "database", "database_team", "instance",
        "current_step", "friendly_status", "maintenance_action", "link_task",
        "started_at", "finished_at"
    )

    readonly_fields = (
        "database", "instance",
        "link_task", "started_at", "finished_at", "current_step", "status",
        "maintenance_action"
    )

    def maintenance_action(self, maintenance_task):
        if (not maintenance_task.is_status_error or
                not maintenance_task.can_do_retry):
            return 'N/A'

        url = maintenance_task.database.get_remove_instance_database_retry_url()
        html = ("<a title='Retry' class='btn btn-info' "
                "href='{}'>Retry</a>").format(url)
        return format_html(html)
