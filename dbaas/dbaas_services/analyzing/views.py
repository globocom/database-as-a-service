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

import models
import csv
import logging
import datetime


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

        header = ['Name', 'VM', 'Env', 'Team', 'Created At', 'In Quarantine', 'Apps Bind Name']
        databases = Database.objects.all()
        database_report = request.POST.get("database_report", "")

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="report.csv"'
        writer = csv.writer(response, csv.excel)
        response.write(u'\ufeff'.encode('utf8'))
        writer.writerow(header)

        for database in databases:
            database_history = DatabaseHistory.objects.filter(database_id=database.id).last()
            try:
                apps_bind_name = database_history.apps_bind_name
            except:
                apps_bind_name = ''
            if database_report == 'database_report':
                hostname = [instance.hostname.hostname.encode("utf-8") for instance in
                            database.infra.instances.all()]
                data = [database.name, hostname, database.environment, database.team,
                        database.created_at, database.is_in_quarantine, apps_bind_name]
                writer.writerow(data)
            else:
                for instance in database.infra.instances.all():
                    data = [database.name, instance.hostname.hostname.encode("utf-8"), database.environment,
                            database.team,
                            database.created_at, database.is_in_quarantine, apps_bind_name]
                    writer.writerow(data)

        return response

