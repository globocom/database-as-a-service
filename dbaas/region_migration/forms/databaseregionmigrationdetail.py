# -*- coding: utf-8 -*-
import logging
from django.forms import models
from ..models import DatabaseRegionMigrationDetail
from django import forms
from django.contrib.admin.widgets import AdminSplitDateTime
from datetime import datetime
LOG = logging.getLogger(__name__)


class DatabaseRegionMigrationDetailForm(models.ModelForm):
    scheduled_for = forms.DateTimeField(initial=datetime.now(),
                                        widget=AdminSplitDateTime)

    def __init__(self, *args, **kwargs):
        super(DatabaseRegionMigrationDetailForm, self).__init__(
            *args, **kwargs)
        self.fields['scheduled_for'] = forms.DateTimeField(
            initial=datetime.now(), widget=AdminSplitDateTime)

    class Meta:
        model = DatabaseRegionMigrationDetail
        fields = ('scheduled_for', )
