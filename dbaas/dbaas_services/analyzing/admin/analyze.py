# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import admin
from dbaas_services.analyzing.service import AnalyzeRepositoryService
from dbaas_services.analyzing.forms import AnalyzeRepositoryForm


class AnalyzeRepositoryAdmin(admin.DjangoServicesAdmin):
    form = AnalyzeRepositoryForm
    service_class = AnalyzeRepositoryService
    search_fields = ("analyzed_at", "database_name", "engine_name",
                     "environment_name", "instance_name",)
    list_filter = ("analyzed_at", "memory_alarm", "cpu_alarm")
    list_display = ("analyzed_at", "database_name", "engine_name",
                    "environment_name", "instance_name", "cpu_alarm",
                    "memory_alarm")
