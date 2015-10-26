# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.forms import models
from dbaas_services.analyzing.models import ExecutionPlan


class ExecutionPlanForm(models.ModelForm):
    class Meta:
        model = ExecutionPlan
