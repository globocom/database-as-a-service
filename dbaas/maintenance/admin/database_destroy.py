# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.conf.urls import patterns, url
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.html import format_html
from notification.tasks import TaskRegister
from .database_maintenance_task import DatabaseMaintenanceTaskAdmin
from ..models import DatabaseDestroy


class DatabaseDestroyAdmin(DatabaseMaintenanceTaskAdmin):

    search_fields = ["name", "infra__name", "user", "task__id", "task__task_id"]
    list_filter = ["plan", "team", "status", "project"]

    list_display = (
        "name", "infra", "team", "project", "environment", "plan_name", "user",
        "current_step", "friendly_status", "maintenance_action", "link_task",
        "started_at", "finished_at"
    )
    readonly_fields = (
        "database", "infra", "plan", "plan_name", "environment", "team",
        "project", "name", "description", "subscribe_to_email_events",
        "is_protected", "user", "link_task", "started_at", "finished_at",
        "current_step", "status", "maintenance_action"
    )

    def maintenance_action(self, maintenance_task):
        if not maintenance_task.is_status_error:
            return 'N/A'

        if not maintenance_task.can_do_retry:
            return 'N/A'

        url_retry = "/admin/maintenance/databasedestroy/{}/retry/".format(maintenance_task.id)
        html_retry = "<a title='Retry' class='btn btn-info' href='{}'>Retry</a>".format(url_retry)

        return format_html(html_retry)

    def get_urls(self):
        base = super(DatabaseDestroyAdmin, self).get_urls()

        admin = patterns(
            '',
            url(
                r'^/?(?P<destroy_id>\d+)/retry/$',
                self.admin_site.admin_view(self.retry_view),
                name="destroy_database_retry"
            ),
        )
        return admin + base

    def retry_view(self, request, destroy_id):
        rollback_from = get_object_or_404(DatabaseDestroy, pk=destroy_id)

        success, redirect = self.check_status(request, destroy_id, 'retry')
        if not success:
            return redirect

        TaskRegister.database_destroy_retry(
            rollback_from=rollback_from,
            user=request.user,
        )

        task_history_url = reverse('admin:notification_taskhistory_changelist')
        query_string = "user={}".format(request.user.username)
        return HttpResponseRedirect('{}?{}'.format(task_history_url, query_string))

    @staticmethod
    def check_status(request, destroy_id, operation):
        destroy = DatabaseDestroy.objects.get(id=destroy_id)

        success = True
        if success and not destroy.is_status_error:
            success = False
            messages.add_message(
                request, messages.ERROR,
                "You can not do {} because destroy status is '{}'".format(
                    operation, destroy.get_status_display()
                ),
            )

        if success and not destroy.can_do_retry:
            success = False
            messages.add_message(
                request, messages.ERROR,
                "Create {} is disabled".format(operation)
            )

        return success, HttpResponseRedirect(
            reverse(
                'admin:maintenance_databasedestroy_change', args=(destroy_id,)
            )
        )
