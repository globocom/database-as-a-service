# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import admin
from ..service.maintenance import MaintenanceService
from ..forms import MaintenanceForm
from django.utils.html import format_html
import logging
LOG = logging.getLogger(__name__)
from .. import models


class MaintenanceAdmin(admin.DjangoServicesAdmin):
    service_class = MaintenanceService
    search_fields = ("scheduled_for", "description", "maximum_workers", "status")
    list_display = ("description", "scheduled_for", "maximum_workers", "affected_hosts_html", "status")
    fields = ( "description", "scheduled_for", "main_script", "rollback_script",
         "host_query","maximum_workers", "status", "celery_task_id", "affected_hosts",
         "query_error",)
    form = MaintenanceForm
    actions = None

    def get_readonly_fields(self, request, obj=None):
        maintenance = obj
        if maintenance and maintenance.status !=models.Maintenance.REJECTED:
            self.change_form_template = "admin/maintenance/maintenance/custom_change_form.html"
        else:
            self.change_form_template = None

        if maintenance and maintenance.celery_task_id:
            return self.fields

        return ('status', 'celery_task_id', 'query_error', 'affected_hosts')


    def affected_hosts_html(self, maintenance):
        html = []
        html.append("<a href='../hostmaintenance/?maintenance__id=%s'>%s</a>" % (maintenance.id, maintenance.affected_hosts))

        return format_html("".join(html))

    affected_hosts_html.short_description = "Affected hosts"


