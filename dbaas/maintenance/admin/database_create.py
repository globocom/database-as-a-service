# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.conf.urls import patterns, url
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.html import format_html
from .database_maintenance_task import DatabaseMaintenanceTaskAdmin
from ..models import DatabaseCreate
from notification.tasks import TaskRegister


class DatabaseCreateAdmin(DatabaseMaintenanceTaskAdmin):

    search_fields = ["name", "infra", "user", "task__id", "task__task_id"]
    list_filter = ["plan", "team", "status", "project"]

    list_display = (
        "name", "infra", "team", "project", "environment", "plan", "user",
        "current_step", "friendly_status", "maintenance_action", "link_task",
        "started_at", "finished_at"
    )
    readonly_fields = (
        "database", "infra", "plan", "environment", "team", "project", "name",
        "description", "subscribe_to_email_events", "is_protected", "user",
        "link_task", "started_at", "finished_at", "current_step", "status",
        "maintenance_action"
    )

    def maintenance_action(self, maintenance_task):
        if not maintenance_task.is_status_error:
            return 'N/A'

        if not maintenance_task.can_do_retry:
            return 'N/A'

        url = "/admin/maintenance/databasecreate/{}/retry/".format(maintenance_task.id)
        html = "<a title='Retry' class='btn btn-info' href='{}'>Retry</a>".format(url)
        return format_html(html)

    def get_urls(self):
        base = super(DatabaseCreateAdmin, self).get_urls()

        admin = patterns(
            '',
            url(
                r'^/?(?P<create_id>\d+)/retry/$',
                self.admin_site.admin_view(self.retry_view),
                name="create_database_retry"
            ),
        )
        return admin + base

    def retry_view(self, request, create_id):
        retry_from = get_object_or_404(DatabaseCreate, pk=create_id)

        error = False
        if not retry_from.is_status_error:
            error = True
            messages.add_message(
                request, messages.ERROR,
                "You can not do retry because create status is '{}'".format(
                    retry_from.get_status_display()
                ),
            )

        if not retry_from.can_do_retry:
            error = True
            messages.add_message(
                request, messages.ERROR, "Create retry is disabled"
            )

        if error:
            return HttpResponseRedirect(
                reverse(
                    'admin:maintenance_databasecreate_change',
                    args=(create_id,)
                )
            )

        TaskRegister.database_create(
            name=retry_from.name,
            plan=retry_from.plan,
            environment=retry_from.environment,
            team=retry_from.team,
            project=retry_from.project,
            description=retry_from.description,
            subscribe_to_email_events=retry_from.subscribe_to_email_events,
            is_protected=retry_from.is_protected,
            user=request.user,
            retry_from=retry_from
        )

        url = reverse('admin:notification_taskhistory_changelist')
        filter = "user={}".format(request.user.username)
        return HttpResponseRedirect('{}?{}'.format(url, filter))
