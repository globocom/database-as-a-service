# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import admin
from ..service.maintenance import MaintenanceService
from ..forms import MaintenanceForm


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

        if maintenance:
            if maintenance.celery_task_id:
                return self.fields

        return ('status', 'celery_task_id',)


