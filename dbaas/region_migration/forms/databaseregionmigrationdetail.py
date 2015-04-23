# -*- coding: utf-8 -*-
import logging
from django.forms import models
from ..models import DatabaseRegionMigrationDetail
from django import forms
from django.forms.widgets import DateTimeInput
from datetime import datetime
LOG = logging.getLogger(__name__)


class DatabaseRegionMigrationDetailForm(models.ModelForm):
    scheduled_for = forms.DateTimeField(initial=datetime.now(),
                                        widget=DateTimeInput)

    def __init__(self, *args, **kwargs):
        super(DatabaseRegionMigrationDetailForm, self).__init__(*args, **kwargs)

    class Meta:
        model = DatabaseRegionMigrationDetail
        fields = ('scheduled_for', )
