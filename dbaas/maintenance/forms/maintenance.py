# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext_lazy as _
import logging
from django import forms
from .. import models
from ..validators import validate_host_query


LOG = logging.getLogger(__name__)

class MaintenanceForm(forms.ModelForm):
    host_query = forms.CharField(widget=forms.Textarea,validators= [validate_host_query])
    class Meta:
        model = models.Maintenance
        fields = ( "description", "scheduled_for", "main_script", "rollback_script",
         "maximum_workers", "status", "celery_task_id",)
