# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.conf.urls import patterns, url
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.html import format_html
from maintenance.models import DatabaseMigrate
from notification.tasks import TaskRegister
from .database_maintenance_task import DatabaseMaintenanceTaskAdmin


class DatabaseMigrateAdmin(DatabaseMaintenanceTaskAdmin):

    list_filter = [
        "status", "database", "environment"
    ]
    search_fields = ("task__id", "task__task_id")

    list_display = (
        "current_step", "database", "origin_environment", "environment",
        "friendly_status", "maintenance_action", "link_task", "started_at",
        "finished_at"
    )
    readonly_fields = (
        "database", "origin_environment", "environment", "link_task",
        "started_at", "finished_at", "current_step", "status",
        "maintenance_action"
    )

    def maintenance_action(self, maintenance_task):
        if not maintenance_task.is_status_error:
            return 'N/A'

        if not maintenance_task.can_do_retry:
            return 'N/A'

        url_retry = "/admin/maintenance/databasemigrate/{}/retry/".format(maintenance_task.id)
        html_retry = "<a title='Retry' class='btn btn-info' href='{}'>Retry</a>".format(url_retry)

        url_rollback = "/admin/maintenance/databasemigrate/{}/rollback/".format(maintenance_task.id)
        html_rollback = "<a title='Rollback' class='btn btn-danger' href='{}'>Rollback</a>".format(url_rollback)

        spaces = '&nbsp' * 3
        html_content = '{}{}{}'.format(html_retry, spaces, html_rollback)
        return format_html(html_content)

    def get_urls(self):
        base = super(DatabaseMigrateAdmin, self).get_urls()
        admin = patterns(
            '',
            url(
                r'^/?(?P<database_migrate_id>\d+)/retry/$',
                self.admin_site.admin_view(self.retry_view),
                name="database_migrate_retry"
            ),
            url(
                r'^/?(?P<database_migrate_id>\d+)/rollback/$',
                self.admin_site.admin_view(self.rollback_view),
                name="database_migrate_rollback"
            ),
        )
        return admin + base

    def retry_view(self, request, database_migrate_id):
        retry_from = get_object_or_404(DatabaseMigrate, pk=database_migrate_id)
        success, redirect = self.check_status(request, retry_from, 'retry')
        if not success:
            return redirect

        TaskRegister.database_migrate(
            retry_from.database, retry_from.environment,
            request.user, retry_from.hosts_zones, retry_from.current_step
        )
        return self.redirect_to_database(retry_from)

    def rollback_view(self, request, database_migrate_id):
        rollback_from = get_object_or_404(DatabaseMigrate, pk=database_migrate_id)
        success, redirect = self.check_status(
            request, rollback_from, 'rollback'
        )
        if not success:
            return redirect
        TaskRegister.database_migrate_rollback(rollback_from, request.user)
        return self.redirect_to_database(rollback_from)

    def check_status(self, request, database_migrate, operation):
        success = True
        if success and not database_migrate.is_status_error:
            success = False
            messages.add_message(
                request, messages.ERROR,
                "You can not do {} because current status is '{}'".format(
                    operation, database_migrate.get_status_display()
                ),
            )

        if success and not database_migrate.can_do_retry:
            success = False
            messages.add_message(
                request, messages.ERROR,
                "{} is disabled".format(operation.capitalize())
            )

        return success, HttpResponseRedirect(
            reverse(
                'admin:maintenance_databasemigrate_change', args=(database_migrate.id,)
            )
        )

    def redirect_to_database(self, maintenance):
        return HttpResponseRedirect(reverse(
            'admin:logical_database_migrate', kwargs={'id': maintenance.database.id})
        )

