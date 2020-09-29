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

    search_fields = ["name", "infra__name", "user", "task__id",
                     "task__task_id"]
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
        "status", "maintenance_action", "task_schedule"
    )

    def maintenance_action(self, maintenance_task):
        if not maintenance_task.is_status_error:
            return 'N/A'

        if not maintenance_task.can_do_retry:
            return 'N/A'

        url_retry = "/admin/maintenance/databasecreate/{}/retry/".format(
            maintenance_task.id
        )
        html_retry = ("<a title='Retry' class='btn btn-info' "
                      "href='{}'>Retry</a>").format(url_retry)

        url_rollback = "/admin/maintenance/databasecreate/{}/rollback/".format(
            maintenance_task.id
        )
        html_rollback = ("<a title='Rollback' class='btn btn-danger' "
                         "href='{}'>Rollback</a>").format(url_rollback)

        spaces = '&nbsp' * 3
        html_content = '{}{}{}'.format(html_retry, spaces, html_rollback)
        return format_html(html_content)

    def get_urls(self):
        base = super(DatabaseCreateAdmin, self).get_urls()

        admin = patterns(
            '',
            url(
                r'^/?(?P<create_id>\d+)/retry/$',
                self.admin_site.admin_view(self.retry_view),
                name="create_database_retry"
            ),
            url(
                r'^/?(?P<create_id>\d+)/rollback/$',
                self.admin_site.admin_view(self.rollback_view),
                name="create_database_rollback"
            ),
        )
        return admin + base

    def retry_view(self, request, create_id):
        retry_from = get_object_or_404(DatabaseCreate, pk=create_id)

        success, redirect = self.check_status(request, create_id, 'retry')
        if not success:
            return redirect

        TaskRegister.database_create(
            name=retry_from.name,
            plan=retry_from.plan,
            environment=retry_from.environment,
            team=retry_from.team,
            project=retry_from.project,
            description=retry_from.description,
            backup_hour=retry_from.infra.backup_hour,
            maintenance_window=retry_from.infra.maintenance_window,
            maintenance_day=retry_from.infra.maintenance_day,
            subscribe_to_email_events=retry_from.subscribe_to_email_events,
            is_protected=retry_from.is_protected,
            user=request.user,
            retry_from=retry_from,
            **{'pool': retry_from.pool}
        )

        url = reverse('admin:notification_taskhistory_changelist')
        filter = "user={}".format(request.user.username)
        return HttpResponseRedirect('{}?{}'.format(url, filter))

    def rollback_view(self, request, create_id):
        rollback_from = get_object_or_404(DatabaseCreate, pk=create_id)

        success, redirect = self.check_status(request, create_id, 'rollback')
        if not success:
            return redirect

        TaskRegister.database_create_rollback(
            rollback_from=rollback_from,
            user=request.user,
        )

        url = reverse('admin:notification_taskhistory_changelist')
        filter = "user={}".format(request.user.username)
        return HttpResponseRedirect('{}?{}'.format(url, filter))

    def check_status(self, request, create_id, operation):
        create = DatabaseCreate.objects.get(id=create_id)

        success = True
        if success and not create.is_status_error:
            success = False
            messages.add_message(
                request, messages.ERROR,
                "You can not do {} because create status is '{}'".format(
                    operation, create.get_status_display()
                ),
            )

        if success and not create.can_do_retry:
            success = False
            messages.add_message(
                request, messages.ERROR,
                "Create {} is disabled".format(operation)
            )

        return success, HttpResponseRedirect(
            reverse(
                'admin:maintenance_databasecreate_change', args=(create_id,)
            )
        )
