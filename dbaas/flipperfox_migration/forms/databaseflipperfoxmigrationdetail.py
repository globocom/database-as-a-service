# -*- coding: utf-8 -*-
import logging
from django.forms import models
from ..models import DatabaseFlipperFoxMigrationDetail
from django import forms
from django.contrib.admin.widgets import AdminSplitDateTime
from datetime import datetime
LOG = logging.getLogger(__name__)


class DatabaseFlipperFoxMigrationDetailForm(models.ModelForm):
    scheduled_for = forms.DateTimeField(initial=datetime.now(),
                                        widget=AdminSplitDateTime)

    def __init__(self, *args, **kwargs):
        super(DatabaseFlipperFoxMigrationDetailForm, self).__init__(
            *args, **kwargs)
        self.fields['scheduled_for'] = forms.DateTimeField(
            initial=datetime.now(), widget=AdminSplitDateTime)

    class Meta:
        model = DatabaseFlipperFoxMigrationDetail
        fields = ('scheduled_for', )
