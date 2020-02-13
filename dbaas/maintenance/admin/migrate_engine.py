# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.html import format_html
from .database_maintenance_task import DatabaseMaintenanceTaskAdmin


class DatabaseMigrateEngineAdmin(DatabaseMaintenanceTaskAdmin):

    list_filter = [
        "database__team", "source_plan", "target_plan", "source_plan__engine",
        "status",
    ]

    list_display = (
        "database", "database_team", "source_plan_name", "target_plan_name",
        "current_step", "friendly_status", "maintenance_action", "link_task",
        "started_at", "finished_at"
    )

    readonly_fields = (
        "database", "source_plan", "source_plan_name", "target_plan",
        "target_plan_name", "link_task", "started_at", "finished_at",
        "status", "maintenance_action", "task_schedule"
    )

    def maintenance_action(self, maintenance_task):
        if (not maintenance_task.is_status_error or
                not maintenance_task.can_do_retry):
            return 'N/A'

        url = maintenance_task.database.get_migrate_engine_retry_url()
        html = ("<a title='Retry' class='btn btn-info' "
                "href='{}'>Retry</a>").format(url)
        return format_html(html)
