# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from django import forms
from .. import models
from ..validators import validate_host_query


LOG = logging.getLogger(__name__)

class HostMaintenanceForm(forms.ModelForm):
    class Meta:
        model = models.HostMaintenance
        fields = ( "started_at", "finished_at", "status")
