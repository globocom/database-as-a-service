# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.conf.urls import patterns, url
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.html import format_html
from .database_maintenance_task import DatabaseMaintenanceTaskAdmin
from ..models import DatabaseConfigureStaticDBParams
from notification.tasks import TaskRegister


class DatabaseConfigureStaticDBParamsAdmin(DatabaseMaintenanceTaskAdmin):
    search_fields = (
        "database__name", "database__databaseinfra__name", "task__id", "task__task_id"
    )

    list_display = (
        "database", "database_team", "current_step", "current_step_class", "friendly_status",
        "maintenance_action", "link_task", "started_at", "finished_at"
    )

    readonly_fields = (
        "database", "task", "started_at", 
        "link_task", "finished_at", "status",
        "maintenance_action", "task_schedule",
        
    )

    def maintenance_action(self, maintenance):
        if not maintenance.is_status_error:
            return 'N/A'

        if not maintenance.can_do_retry:
            return 'N/A'

        url = "/admin/maintenance/databaseconfigurestaticdbparams/{}/retry/".format(
            maintenance.id
        )
        html = ("<a title='Retry' class='btn btn-info' "
                "href='{}'>Retry</a>").format(url)
        return format_html(html)

    def get_urls(self):
        base = super(DatabaseConfigureStaticDBParamsAdmin, self).get_urls()

        admin = patterns(
            '',
            url(
                r'^/?(?P<configure_static_db_params_id>\d+)/retry/$',
                self.admin_site.admin_view(self.retry_view),
                name="configure_static_db_params_retry"
            ),
        )
        return admin + base

    def retry_view(self, request, configure_static_db_params_id):
        retry_from = get_object_or_404(DatabaseConfigureStaticDBParams, pk=configure_static_db_params_id)

        error = False
        if not retry_from.is_status_error:
            error = True
            messages.add_message(
                request, messages.ERROR,
                "You can not do retry because configure static db params status is '{}'".format(
                    retry_from.get_status_display()
                ),
            )

        if not retry_from.can_do_retry:
            error = True
            messages.add_message(
                request, messages.ERROR, "Configure Static DB Params retry is disabled"
            )

        if error:
            return HttpResponseRedirect(
                reverse(
                    'admin:maintenance_configurestaticdbparams_change',
                    args=(configure_static_db_params_id,)
                )
            )

        TaskRegister.configure_static_db_params(
            database=retry_from.database,
            user=request.user,
            retry_from=retry_from
        )

        url = reverse('admin:notification_taskhistory_changelist')
        filters = "user={}".format(request.user.username)
        return HttpResponseRedirect('{}?{}'.format(url, filters))
