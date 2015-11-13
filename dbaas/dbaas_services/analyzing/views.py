# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.views.generic import ListView
from django.shortcuts import render
import models


class SubUsedResourceReport(ListView):
    def get(self, request, *args, **kwargs):
        reports = models.AnalyzeRepository.objects.all().order_by('-analyzed_at').values('analyzed_at').distinct()

        report_links = (report['analyzed_at'] for report in reports)
        return render(request, 'reports/index.html', {'reports': report_links})
