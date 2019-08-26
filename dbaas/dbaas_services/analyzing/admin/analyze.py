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
    list_filter = ("analyzed_at", "memory_alarm", "cpu_alarm", "volume_alarm",
                   "engine_name", "environment_name", "databaseinfra_name")
    list_display = ("analyzed_at", "databaseinfra_name", "database_name_link",
                    "engine_name", "environment_name", "database_metrics_link",
                    "cpu_threshold_msg", "memory_threshold_msg",
                    "volume_threshold_msg", "get_database_team")

    def database_name_link(self, analyze_repository):
        try:
            database = Database.objects.get(
                name=analyze_repository.database_name,
                databaseinfra__name=analyze_repository.databaseinfra_name
            )
        except Database.DoesNotExist:
            return analyze_repository.database_name
        else:
            return format_html(
                "<a href=/admin/logical/database/{}>{}</a>".format(
                    database.id, database.name
                )
            )
    database_name_link.short_description = "Database name"
    database_name_link.admin_order_field = "database_name"

    def database_metrics_link(self, analyze_repository):
        try:
            database = Database.objects.get(
                name=analyze_repository.database_name,
                databaseinfra__name=analyze_repository.databaseinfra_name
            )
        except Database.DoesNotExist:
            html_link = analyze_repository.instance_name
        else:
            host_metrics_url = '{}?hostname={}'.format(
                database.get_metrics_url(),
                analyze_repository.instance_name
            )
            html_link = "<a href={}>{}</a>".format(
                host_metrics_url,
                analyze_repository.instance_name
            )

        return format_html(html_link)
    database_metrics_link.short_description = "Instance name"
    database_metrics_link.admin_order_field = "instance_name"

    def get_database_team(self, analyze_repository):
        try:
            database = Database.objects.get(
                name=analyze_repository.database_name,
                databaseinfra__name=analyze_repository.databaseinfra_name
            )
        except Database.DoesNotExist:
            team = ''
        else:
            team = database.team.name

        return team
    get_database_team.short_description = "Team"

    def __format_alarm_msg(self, analyze_repository, alarm_attr,
                           threshold_attr):
        alarm = getattr(analyze_repository, alarm_attr)
        if alarm:
            msg = self.__format_alarm_true(analyze_repository, threshold_attr)
        else:
            msg = self.__format_alarm_false()
        return format_html(msg)

    def __format_alarm_true(self, analyze_repository, threshold_attr):
        threshold = getattr(analyze_repository, threshold_attr)
        return ('<span class="label label-important">'
                'Using less than {}%</span>'.format(threshold))

    def __format_alarm_false(self,):
        return '<span class="label label-success">OK</span>'

    def cpu_threshold_msg(self, analyze_repository):
        return self.__format_alarm_msg(
            analyze_repository,
            'cpu_alarm',
            'cpu_threshold'
        )
    cpu_threshold_msg.short_description = "CPU"
    cpu_threshold_msg.admin_order_field = "cpu_alarm"

    def memory_threshold_msg(self, analyze_repository):
        return self.__format_alarm_msg(
            analyze_repository,
            'memory_alarm',
            'memory_threshold'
        )
    memory_threshold_msg.short_description = "Memory"
    memory_threshold_msg.admin_order_field = "memory_alarm"

    def volume_threshold_msg(self, analyze_repository):
        return self.__format_alarm_msg(
            analyze_repository,
            'volume_alarm',
            'volume_threshold'
        )
    volume_threshold_msg.short_description = "Volume"
    volume_threshold_msg.admin_order_field = "volume_alarm"
