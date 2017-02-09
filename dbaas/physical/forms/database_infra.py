# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from django import forms
from .. import models

log = logging.getLogger(__name__)


class DatabaseInfraForm(forms.ModelForm):

    class Meta:
        model = models.DatabaseInfra

    def __init__(self, *args, **kwargs):
        if args and 'disk_offering' in args[0]:
            disk_offering = args[0]['disk_offering']
            plan_id = args[0]['plan']
            if not disk_offering and plan_id:
                plan = models.Plan.objects.get(id=plan_id)
                if plan.disk_offering:
                    args[0]['disk_offering'] = plan.disk_offering.id

        super(DatabaseInfraForm, self).__init__(*args, **kwargs)
