# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from django import forms
from .. import models


LOG = logging.getLogger(__name__)

class MaintenanceForm(forms.ModelForm):
    class Meta:
        model = models.Maintenance
        fields = ( "description", "scheduled_for", "main_script", "rollback_script",
         "maximum_workers", "status", "celery_task_id",)
    
