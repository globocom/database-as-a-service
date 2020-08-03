# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.html import format_html
from .database_maintenance_task import DatabaseMaintenanceTaskAdmin


class DatabaseChangePersistenceAdmin(DatabaseMaintenanceTaskAdmin):

    list_filter = [
        "database__team", "status",
    ]

    list_display = (
        "database", "database_team",
        "current_step", "friendly_status", "maintenance_action", "link_task",
         "source_plan", "target_plan",
        "started_at", "finished_at"
    )

    readonly_fields = (
        "database", "link_task", "started_at", "finished_at",
        "status", "maintenance_action", "task_schedule",
        "source_plan", "target_plan",
    )

    def maintenance_action(self, maintenance_task):
        if (not maintenance_task.is_status_error or
                not maintenance_task.can_do_retry):
            return 'N/A'

        url = maintenance_task.database.get_change_persistence_retry_url()
        html = ("<a title='Retry' class='btn btn-info' "
                "href='{}'>Retry</a>").format(url)
        return format_html(html)
