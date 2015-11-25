# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.views.generic import ListView
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from notification.models import TaskHistory
import models


class SubUsedResourceReport(ListView):
    def get(self, request, *args, **kwargs):
        reports = models.AnalyzeRepository.objects.all().order_by('-analyzed_at').values('analyzed_at').distinct()

        report_links = (report['analyzed_at'] for report in reports)
        return render(request, 'reports/index.html', {'reports': report_links})

    def post(self, request, *args, **kwargs):
        from dbaas_services.analyzing.tasks import analyze_databases

        task_history = TaskHistory()
        task_history.task_name = "analyze_databases"
        task_history.task_status = task_history.STATUS_WAITING
        task_history.arguments = "Waiting to start"
        task_history.save()
        analyze_databases.delay(task_history=task_history)
        url = reverse('admin:notification_taskhistory_changelist')
        return HttpResponseRedirect(url)
