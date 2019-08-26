# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.views.generic import ListView
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from notification.tasks import TaskRegister
import models


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
