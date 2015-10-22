# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.forms import models
from dbaas_services.analyzing.models import AnalyzeRepository


class AnalyzeRepositoryForm(models.ModelForm):
    class Meta:
        model = AnalyzeRepository
