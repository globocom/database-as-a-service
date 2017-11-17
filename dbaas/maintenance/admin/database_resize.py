# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.html import format_html
from .database_maintenance_task import DatabaseMaintenanceTaskAdmin


class DatabaseResizeAdmin(DatabaseMaintenanceTaskAdmin):
    search_fields = ("database__name", "source_offer__name",
                     "target_offer__name", "task__id", "task__task_id")

    list_display = (
        "database", "database_team", "source_offer", "target_offer",
        "current_step", "friendly_status", "maintenance_action", "link_task",
        "started_at", "finished_at"
    )

    readonly_fields = (
        "database", "source_offer", "target_offer", "link_task", "started_at",
        "finished_at", "current_step", "status", "maintenance_action"
    )

    def maintenance_action(self, maintenance):
        if not maintenance.is_status_error or not maintenance.can_do_retry:
            return 'N/A'

        url_retry = maintenance.database.get_resize_retry_url()
        html_retry = "<a title='Retry' class='btn btn-warning' href='{}'>Retry</a>".format(url_retry)

        url_rollback = maintenance.database.get_resize_rollback_url()
        html_rollback = "<a title='Rollback' class='btn btn-danger' href='{}'>Rollback</a>".format(url_rollback)

        spaces = '&nbsp' * 3
        html_content = '{}{}{}'.format(html_rollback, spaces, html_retry)
        return format_html(html_content)
