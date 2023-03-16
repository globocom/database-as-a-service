# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.views.generic import ListView
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from rest_framework.response import Response
from rest_framework import status
from notification.tasks import TaskRegister
from logical.models import Database, DatabaseHistory
from dbaas.middleware import UserMiddleware
from django.conf import settings
from account.models import Team, Role
from datetime import datetime

import models
import csv
import logging


LOG = logging.getLogger(__name__)


class SubUsedResourceReport(ListView):
    def get(self, request, *args, **kwargs):
        reports = (models.AnalyzeRepository.objects.all()
                   .order_by('-analyzed_at')
                   .values('analyzed_at')
                   .distinct())

        report_links = (report['analyzed_at'] for report in reports)
        return render(request, 'reports/index.html', {'reports': report_links})

    def post(self, request, *args, **kwargs):
        TaskRegister.databases_analyze()

        url = reverse('admin:notification_taskhistory_changelist')
        return HttpResponseRedirect(url)


class DatabaseReport(ListView):

    def has_perm(self, request):
        UserMiddleware.set_current_user(request.user)
        from_teams = [x.role for x in Team.objects.filter(users=request.user)]
        role_dba = Role.objects.get(name='role_dba')

        if role_dba not in from_teams:
            return render(request, 'databases/index.html', {"has_perm": False})

    def get(self, request, *args, **kwargs):
        self.has_perm(request)

        return render(request, 'databases/index.html', {"has_perm": True})

    def post(self, request, *args, **kwargs):
        self.has_perm(request)

        database_report = request.POST.get("database_report", "")

        if database_report == 'database_report':
            return self.default_database_report()
        else:
            return self.vm_by_line_database_report()

    def vm_by_line_database_report(self):

        header = [
            'Name', 'Observacao', 'VM', 'Env', 'Team', 'Team Name', 'Team Area', 'Email', 'Emergency Contacts',
            'Team Organization', 'Created At', 'In Quarantine', 'Apps Bind Name', 'CPU', 'Memory in MB', 'Disk in Gb',
            'Engine type'
        ]

        databases = Database.objects.all()
        response = HttpResponse(content_type='text/csv')

        filename = 'dbaas_databases_vm_by_line-' + datetime.now().strftime("%Y-%m-%d") + ".csv"

        response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
        writer = csv.writer(response, csv.excel)
        response.write(u'\ufeff'.encode('utf8'))
        writer.writerow(header)

        for database in databases:
            for instance in database.infra.instances.all():
                try:
                    data = [
                        database.name,
                        database.attention_description,
                        instance.hostname.hostname.encode("utf-8"),
                        database.environment,
                        database.team,
                        database.team.name,
                        database.team.team_area,
                        database.team.email,
                        database.team.contacts,
                        database.team.organization.name,
                        database.created_at,
                        database.is_in_quarantine,
                        database.apps_bind_name,
                        database.infra.offering.cpus,
                        database.infra.offering.memory_size_mb,
                        database.infra.disk_offering.size_gb(),
                        database.engine_type
                    ]
                    writer.writerow(data)
                except Exception as e:
                    data = [
                        database.name,
                        database.attention_description,
                        instance.hostname.hostname.encode("utf-8"),
                        database.environment,
                        database.team,
                        database.team.name,
                        database.team.team_area,
                        database.team.email,
                        database.team.contacts,
                        database.team.organization.name,
                        database.created_at,
                        database.is_in_quarantine,
                        database.apps_bind_name,
                        '',
                        '',
                        '',
                        database.engine_type
                    ]
                    writer.writerow(data)
                    LOG.error('Error generating csv. Error: {}'.format(e))

        return response

    def default_database_report(self):

        header = [
            'Name', 'Observacao', 'VM', 'Env', 'Team', 'Team Name', 'Team Area', 'Email', 'Emergency Contacts',
            'Team Organization', 'Created At', 'In Quarantine', 'Apps Bind Name', 'CPU', 'Memory in MB', 'Disk in Gb',
            'Engine type'
        ]
        databases = Database.objects.all()
        response = HttpResponse(content_type='text/csv')

        filename = 'dbaas_databases-' + datetime.now().strftime("%Y-%m-%d") + ".csv"
        response['Content-Disposition'] = 'attachment; filename="' + filename + '"'

        writer = csv.writer(response, csv.excel)
        response.write(u'\ufeff'.encode('utf8'))
        writer.writerow(header)

        for database in databases:
            hostname = [
                instance.hostname.hostname.encode("utf-8") for instance in database.infra.instances.all()
            ]
            try:
                data = [
                    database.name,
                    database.attention_description,
                    hostname,
                    database.environment,
                    database.team,
                    database.team.name,
                    database.team.team_area,
                    database.team.email,
                    database.team.contacts,
                    database.team.organization.name,
                    database.created_at,
                    database.is_in_quarantine,
                    database.apps_bind_name,
                    database.infra.offering.cpus,
                    database.infra.offering.memory_size_mb,
                    database.infra.disk_offering.size_gb(),
                    database.engine_type
                ]
                writer.writerow(data)

            except Exception as e:
                data = [
                    database.name,
                    database.attention_description,
                    hostname,
                    database.environment,
                    database.team,
                    database.team.name,
                    database.team.team_area,
                    database.team.email,
                    database.team.contacts,
                    database.team.organization.name,
                    database.created_at,
                    database.is_in_quarantine,
                    database.apps_bind_name,
                    '',
                    '',
                    '',
                    database.engine_type
                ]
                writer.writerow(data)
                LOG.error('Error generating csv. Error: {}'. format(e))

        return response