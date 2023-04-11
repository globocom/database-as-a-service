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

        if role_dba in from_teams:
            return render(request, 'databases/index.html', {"has_perm": True})

    def get(self, request, *args, **kwargs):
        if self.has_perm(request):
           return render(request, 'databases/index.html', {"has_perm": True})

        return HttpResponseRedirect(reverse('admin:index'))


    def post(self, request, *args, **kwargs):
        if self.has_perm(request):
            database_report = request.POST.get("database_report", "")


            if database_report == 'database_report':
                return self.default_database_report()
            else:
                return self.vm_by_line_database_report()

        return HttpResponseRedirect(reverse('admin:index'))


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
                data = [
                    database.name,
                    database.attention_description,
                    instance.hostname.hostname.encode("utf-8"),
                    database.environment,
                    self._check_values(database, 'team'),
                    self._check_values(database, 'team_name'),
                    self._check_values(database, 'team_area'),
                    self._check_values(database, 'team_email'),
                    self._check_values(database, 'team_contacts'),
                    self._check_values(database, 'team_organization'),
                    database.created_at,
                    database.is_in_quarantine,
                    database.apps_bind_name,
                    self._check_values(database, 'cpu'),
                    self._check_values(database, 'memory_size'),
                    self._check_values(database, 'disk_size'),
                    database.engine_type
                ]
                writer.writerow(data)

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
            data = [
                database.name,
                database.attention_description,
                hostname,
                database.environment,
                self._check_values(database, 'team'),
                self._check_values(database, 'team_name'),
                self._check_values(database, 'team_area'),
                self._check_values(database, 'team_email'),
                self._check_values(database, 'team_contacts'),
                self._check_values(database, 'team_organization'),
                database.created_at,
                database.is_in_quarantine,
                database.apps_bind_name,
                self._check_values(database, 'cpu'),
                self._check_values(database, 'memory_size'),
                self._check_values(database, 'disk_size'),
                database.engine_type
            ]
            writer.writerow(data)

        return response

    def _check_values(self, database, attr):
        if attr == 'team':
            try:
                return database.team
            except:
                return ''

        if attr == 'team_name':
            try:
                return database.team.name
            except:
                return ''

        if attr == 'team_area':
            try:
                return database.team.team_area
            except:
                return ''

        if attr == 'team_email':
            try:
                return database.team.email
            except:
                return ''

        if attr == 'team_contacts':
            try:
                return database.team.contacts
            except:
                return ''

        if attr == 'team_organization':
            try:
                return database.team.organization.name
            except:
                return ''

        if attr == 'cpu':
            try:
                return database.infra.offering.cpus
            except:
                return 0

        if attr == 'memory_size':
            try:
                return database.infra.offering.memory_size_mb
            except:
                return 0

        if attr == 'disk_size':
            try:
                return database.infra.disk_offering.size_gb()
            except:
                return 0
