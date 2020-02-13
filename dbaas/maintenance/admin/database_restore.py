# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.conf.urls import patterns, url
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.html import format_html
from .database_maintenance_task import DatabaseMaintenanceTaskAdmin
from ..models import DatabaseRestore
from notification.tasks import TaskRegister


class DatabaseRestoreAdmin(DatabaseMaintenanceTaskAdmin):
    search_fields = (
        "database__name", "database__databaseinfra__name", "task__id",
        "task__task_id", "group__id"
    )

    list_display = (
        "database", "database_team", "current_step", "friendly_status",
        "maintenance_action", "link_task", "started_at", "finished_at"
    )

    readonly_fields = (
        "database", "task", "group", "new_group", "started_at", "link_task",
        "finished_at", "status", "maintenance_action", "task_schedule"
    )

    def maintenance_action(self, maintenance):
        if not maintenance.is_status_error:
            return 'N/A'

        if not maintenance.can_do_retry:
            return 'N/A'

        url = "/admin/maintenance/databaserestore/{}/retry/".format(
            maintenance.id
        )
        html = ("<a title='Retry' class='btn btn-info' "
                "href='{}'>Retry</a>").format(url)
        return format_html(html)

    def get_urls(self):
        base = super(DatabaseRestoreAdmin, self).get_urls()

        admin = patterns(
            '',
            url(
                r'^/?(?P<restore_id>\d+)/retry/$',
                self.admin_site.admin_view(self.retry_view),
                name="restore_database_retry"
            ),
        )
        return admin + base

    def retry_view(self, request, restore_id):
        retry_from = get_object_or_404(DatabaseRestore, pk=restore_id)

        error = False
        if not retry_from.is_status_error:
            error = True
            messages.add_message(
                request, messages.ERROR,
                "You can not do retry because restore status is '{}'".format(
                    retry_from.get_status_display()
                ),
            )

        if not retry_from.can_do_retry:
            error = True
            messages.add_message(
                request, messages.ERROR, "Restore retry is disabled"
            )

        if error:
            return HttpResponseRedirect(
                reverse(
                    'admin:maintenance_databaserestore_change',
                    args=(restore_id,)
                )
            )

        TaskRegister.restore_snapshot(
            database=retry_from.database,
            snapshot=retry_from.group.backups.first().id,
            user=request.user,
            retry_from=retry_from
        )

        url = reverse('admin:notification_taskhistory_changelist')
        filter = "user={}".format(request.user.username)
        return HttpResponseRedirect('{}?{}'.format(url, filter))
