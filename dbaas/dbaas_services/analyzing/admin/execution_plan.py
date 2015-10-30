# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import admin
from dbaas_services.analyzing.service import ExecutionPlanService
from dbaas_services.analyzing.forms import ExecutionPlanForm


class ExecutionPlanAdmin(admin.DjangoServicesAdmin):
    form = ExecutionPlanForm
    service_class = ExecutionPlanService
    list_display = ("plan_name", "metrics", "threshold",
                    "proccess_function", "adapter", "alarm_repository_attr",)
