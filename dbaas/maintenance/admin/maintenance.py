# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import admin
from ..service.maintenance import MaintenanceService
from ..forms import MaintenanceForm
import logging
from django.contrib import messages
LOG = logging.getLogger(__name__)
from .. import models
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

class MaintenanceAdmin(admin.DjangoServicesAdmin):
    service_class = MaintenanceService
    search_fields = ("scheduled_for", "description", "maximum_workers", 'status')
    list_display = ("scheduled_for", "description", "maximum_workers", 'status')
    fields = ( "description", "scheduled_for", "main_script", "rollback_script",
         "host_query","maximum_workers", "status", "celery_task_id",)
    save_on_top = True
    form = MaintenanceForm

    def get_readonly_fields(self, request, obj=None):
        maintenance = obj
        if maintenance and maintenance.celery_task_id:
            LOG.debug("All fields are read_only!")
            return self.fields

        return ('status', 'celery_task_id',)


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



