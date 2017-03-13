from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.html import format_html
from maintenance.models import DatabaseResize


class DatabaseResizeAdmin(admin.ModelAdmin):
    list_select_related = None
    search_fields = ("database__name", "source_offer__name", "target_offer__name", "task__id", "task__task_id")
    list_filter = [
        "database__team", "status",
    ]
    exclude = ("task", "can_do_retry")

    actions = None
    list_display = (
        "database", "database_team", "source_offer", "target_offer",
        "current_step", "friendly_status", "resize_action", "link_task",
        "started_at", "finished_at"
    )

    readonly_fields = (
        "database", "source_offer", "target_offer", "link_task", "started_at",
        "finished_at", "current_step", "status", "resize_action"
    )

    ordering = ["-started_at"]

    def friendly_status(self, resize):
        html_waiting = '<span class="label label-warning">Waiting</span>'
        html_running = '<span class="label label-success">Running</span>'
        html_error = '<span class="label label-important">Error</span>'
        html_success = '<span class="label label-info">Success</span>'

        html_status = ''
        if resize.status == DatabaseResize.WAITING:
            html_status = html_waiting
        elif resize.status == DatabaseResize.RUNNING:
            html_status = html_running
        elif resize.status == DatabaseResize.ERROR:
            html_status = html_error
        elif resize.status == DatabaseResize.SUCCESS:
            html_status = html_success

        return format_html(html_status)
    friendly_status.short_description = "Status"

    def database_team(self, resize):
        return resize.database.team.name
    database_team.short_description = "Team"

    def link_task(self, resize):
        url = reverse(
            'admin:notification_taskhistory_change', args=[resize.task.id]
        )
        return format_html(
            "<a href={}>{}</a>".format(url, resize.task.id)
        )
    link_task.short_description = "Task"

    def resize_action(self, resize):
        if not resize.is_status_error or not resize.can_do_retry:
            return 'N/A'

        url = resize.database.get_resize_retry_url()
        html = "<a title='Retry' class='btn btn-info' href='{}'>Retry</a>".format(url)
        return format_html(html)
    resize_action.short_description = "Action"

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False
