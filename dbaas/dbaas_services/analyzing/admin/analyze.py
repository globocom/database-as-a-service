# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import admin
from dbaas_services.analyzing.service import AnalyzeRepositoryService
from dbaas_services.analyzing.forms import AnalyzeRepositoryForm
from logical.models import Database
from django.utils.html import format_html


class AnalyzeRepositoryAdmin(admin.DjangoServicesAdmin):
    form = AnalyzeRepositoryForm
    service_class = AnalyzeRepositoryService
    search_fields = ("database_name", "engine_name",
                     "environment_name", "instance_name", "databaseinfra_name")
    list_filter = ("analyzed_at", "memory_alarm", "cpu_alarm", "volume_alarm", "engine_name",
                   "environment_name", "databaseinfra_name")
    list_display = ("analyzed_at", "databaseinfra_name", "database_name", "engine_name",
                    "environment_name", "database_metrics_link", "cpu_alarm",
                    "memory_alarm", "volume_alarm")

    def database_metrics_link(self, analyze_repository):
        try:
            database = Database.objects.get(name=analyze_repository.database_name,
                                            databaseinfra__name=analyze_repository.databaseinfra_name)
        except Database.DoesNotExist:
            html_link = analyze_repository.instance_name
        else:
            html_link = "<a href={}>{}</a>".format(database.get_metrics_url(),
                                                   analyze_repository.instance_name)

        return format_html(html_link)

    database_metrics_link.short_description = "Instance name"
