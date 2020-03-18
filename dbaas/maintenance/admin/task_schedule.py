# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import admin
from maintenance.service.task_schedule import TaskScheduleService


class TaskScheduleAdmin(admin.DjangoServicesAdmin):
    service_class = TaskScheduleService
    list_display = ("method_path", "database", "status", "scheduled_for",
                    "finished_at")
    search_fields = ('method_path', 'database__name')

    list_filter = (
        "status",
    )
