# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import admin
from ..service.maintenance import MaintenanceService
from ..forms import MaintenanceForm
from django.utils.html import format_html, escape
import logging
from django.contrib import messages
LOG = logging.getLogger(__name__)
from .. import models
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

class MaintenanceAdmin(admin.DjangoServicesAdmin):
    service_class = MaintenanceService
    search_fields = ("scheduled_for", "description", "maximum_workers", "status")
    list_display = ("description", "scheduled_for", "maximum_workers", "affected_hosts_html", "status")
    fields = ( "description", "scheduled_for", "main_script", "rollback_script",
         "host_query","maximum_workers", "status", "celery_task_id", "affected_hosts",
         "query_error",)
    form = MaintenanceForm

    def get_readonly_fields(self, request, obj=None):
        maintenance = obj
        if maintenance and maintenance.status !=models.Maintenance.REJECTED:
            self.change_form_template = "admin/maintenance/maintenance/custom_change_form.html"
        else:
            self.change_form_template = None

        if maintenance and maintenance.celery_task_id:
            return self.fields

        return ('status', 'celery_task_id', 'query_error', 'affected_hosts')

    def get_change_form_template(self, *args, **kwargs):
        import pdb
        pdb.set_trace()


    def delete_view(self, request, object_id, extra_context=None):
        maintenance = models.Maintenance.objects.get(id=object_id)
        if maintenance.status ==  maintenance.RUNNING:
            self.message_user(request, "Task is running and cannot be deleted now. \
                You must wait it to finish", level=messages.ERROR)

            LOG.info("Maintenance: can not be deleted!".format(maintenance))
            return HttpResponseRedirect(
                reverse('maintenance:maintenance_maintenance_changelist'))

        LOG.info("Maintenance: can be deleted!".format(maintenance))
        return super(MaintenanceAdmin, self).delete_view(request,
            object_id, extra_context)


    def affected_hosts_html(self, maintenance):
        html = []
        html.append("<a href='../hostmaintenance/?maintenance__id=%s'>%s</a>" % (maintenance.id, maintenance.affected_hosts))

        return format_html("".join(html))

    affected_hosts_html.short_description = "Affected hosts"


