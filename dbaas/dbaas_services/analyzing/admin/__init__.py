# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from dbaas_services.analyzing import models
from dbaas_services.analyzing.admin.analyze import AnalyzeRepositoryAdmin
from dbaas_services.analyzing.admin.execution_plan import ExecutionPlanAdmin


admin.site.register(models.AnalyzeRepository, AnalyzeRepositoryAdmin)
admin.site.register(models.ExecutionPlan, ExecutionPlanAdmin)
