# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.conf.urls import patterns, url
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.html import format_html
from maintenance.models import RestartDatabase
from notification.tasks import TaskRegister
from .database_maintenance_task import DatabaseMaintenanceTaskAdmin


class RestartDatabaseAdmin(DatabaseMaintenanceTaskAdmin):

    list_filter = [
        "status"
    ]
    search_fields = ("task__id", "task__task_id")

    list_display = (
        "current_step", "database", "friendly_status",
        "maintenance_action", "link_task",
        "started_at", "finished_at"
    )
    readonly_fields = (
        "database", "link_task",
        "started_at", "finished_at", "status", "task_schedule",
        "maintenance_action"
    )

    def maintenance_action(self, maintenance_task):
        if not maintenance_task.is_status_error:
            return 'N/A'

        if not maintenance_task.can_do_retry:
            return 'N/A'

        url_retry = "/admin/maintenance/restartdatabase/{}/retry/".format(
            maintenance_task.id
        )
        html_retry = (
            "<a title='Retry' class='btn btn-info' href='{}'>Retry</a>".format(
                url_retry
            )
        )
        return format_html(html_retry)

    def get_urls(self):
        base = super(RestartDatabaseAdmin, self).get_urls()
        admin = patterns(
            '',
            url(
                r'^/?(?P<manager_id>\d+)/retry/$',
                self.admin_site.admin_view(self.retry_view),
                name="restart_database_retry"
            )
        )
        return admin + base

    def retry_view(self, request, manager_id):
        retry_from = get_object_or_404(RestartDatabase, pk=manager_id)
        success, redirect = self.check_status(request, retry_from, 'retry')
        if not success:
            return redirect
        TaskRegister.restart_database(
            database=retry_from.database,
            user=request.user,
            since_step=retry_from.current_step,
            step_manager=retry_from
        )
        return self.redirect_to_database(retry_from)

    def check_status(self, request, step_manager, operation):
        success = True
        if success and not step_manager.is_status_error:
            success = False
            messages.add_message(
                request, messages.ERROR,
                "You can not do {} because current status is '{}'".format(
                    operation, step_manager.get_status_display()
                ),
            )

        if success and not step_manager.can_do_retry:
            success = False
            messages.add_message(
                request, messages.ERROR,
                "{} is disabled".format(operation.capitalize())
            )

        return success, HttpResponseRedirect(
            reverse(
                'admin:maintenance_restartdatabase_change',
                args=(step_manager.id,)
            )
        )

    def redirect_to_database(self, maintenance):
        return HttpResponseRedirect(reverse(
            'admin:logical_database_hosts', kwargs={
                'id': maintenance.database.id
            })
        )
