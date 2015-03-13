# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import admin
from ..models import Maintenance
from ..service.maintenance import MaintenanceService



class MaintenanceAdmin(admin.DjangoServicesAdmin):
    service_class = MaintenanceService
    search_fields = ("scheduled_for", "description", "maximum_workers", 'status')
    list_display = ("scheduled_for", "description", "maximum_workers", 'status')
    fields = ( "description", "scheduled_for", "main_script", "rollback_script",
         "host_query","maximum_workers", "status", "celery_task_id",)
    save_on_top = True
    readonly_fields = ('status', 'celery_task_id')


    def change_view(self, request, object_id, form_url='', extra_context=None):
        maintenance = Maintenance.objects.get(id=object_id)

        if maintenance.celery_task_id:
            self.readonly_fields = self.fields

        return super(MaintenanceAdmin, self).change_view(request,
            object_id, form_url, extra_context=extra_context)

    def add_view(self, request, form_url='', extra_context=None):
        return super(MaintenanceAdmin, self).add_view(request, form_url,
            extra_context)


