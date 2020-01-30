# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.conf.urls import patterns, url
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.html import format_html
from maintenance.admin.database_maintenance_task import (
    DatabaseMaintenanceTaskAdmin)
from maintenance.models import DatabaseClone
from notification.tasks import TaskRegister


class DatabaseCloneAdmin(DatabaseMaintenanceTaskAdmin):

    search_fields = ["name", "infra__name", "user", "task__id",
                     "task__task_id"]
    list_filter = ["plan", "status"]

    list_display = (
        "name", "infra", "environment", "user",
        "current_step", "friendly_status", "maintenance_action", "link_task",
        "started_at", "finished_at"
    )
    readonly_fields = (
        "database", "infra", "plan", "environment",
        "name", "origin_database", "user", "link_task",
        "started_at", "finished_at", "current_step", "status",
        "maintenance_action"
    )

    def maintenance_action(self, maintenance_task):
        if not maintenance_task.is_status_error:
            return 'N/A'

        if not maintenance_task.can_do_retry:
            return 'N/A'

        url_retry = "/admin/maintenance/databaseclone/{}/retry/".format(
            maintenance_task.id
        )
        html_retry = ("<a title='Retry' class='btn btn-info' "
                      "href='{}'>Retry</a>").format(url_retry)

        url_rollback = "/admin/maintenance/databaseclone/{}/rollback/".format(
            maintenance_task.id
        )
        html_rollback = ("<a title='Rollback' class='btn btn-danger' "
                         "href='{}'>Rollback</a>").format(url_rollback)

        spaces = '&nbsp' * 3
        html_content = '{}{}{}'.format(html_retry, spaces, html_rollback)
        return format_html(html_content)

    def get_urls(self):
        base = super(DatabaseCloneAdmin, self).get_urls()

        admin = patterns(
            '',
            url(
                r'^/?(?P<clone_id>\d+)/retry/$',
                self.admin_site.admin_view(self.retry_view),
                name="clone_database_retry"
            ),
            url(
                r'^/?(?P<clone_id>\d+)/rollback/$',
                self.admin_site.admin_view(self.rollback_view),
                name="clone_database_rollback"
            ),
        )
        return admin + base

    def retry_view(self, request, clone_id):
        retry_from = get_object_or_404(DatabaseClone, pk=clone_id)

        success, redirect = self.check_status(request, clone_id, 'retry')
        if not success:
            return redirect

        TaskRegister.database_clone(
            clone_name=retry_from.name,
            plan=retry_from.plan,
            environment=retry_from.environment,
            user=request.user,
            origin_database=retry_from.origin_database,
            retry_from=retry_from
        )

        url = reverse('admin:notification_taskhistory_changelist')
        filter = "user={}".format(request.user.username)
        return HttpResponseRedirect('{}?{}'.format(url, filter))

    def rollback_view(self, request, clone_id):
        rollback_from = get_object_or_404(DatabaseClone, pk=clone_id)

        success, redirect = self.check_status(request, clone_id, 'rollback')
        if not success:
            return redirect

        TaskRegister.database_clone_rollback(
            rollback_from=rollback_from,
            user=request.user,
        )

        url = reverse('admin:notification_taskhistory_changelist')
        filter = "user={}".format(request.user.username)
        return HttpResponseRedirect('{}?{}'.format(url, filter))

    def check_status(self, request, clone_id, operation):
        create = DatabaseClone.objects.get(id=clone_id)

        success = True
        if success and not create.is_status_error:
            success = False
            messages.add_message(
                request, messages.ERROR,
                "You can not do {} because clone status is '{}'".format(
                    operation, create.get_status_display()
                ),
            )

        if success and not create.can_do_retry:
            success = False
            messages.add_message(
                request, messages.ERROR,
                "Clone {} is disabled".format(operation)
            )

        return success, HttpResponseRedirect(
            reverse(
                'admin:maintenance_databaseclone_change', args=(clone_id,)
            )
        )
