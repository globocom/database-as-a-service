# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from django.utils.translation import ugettext_lazy as _
from django import forms
from .. import models

log = logging.getLogger(__name__)


class DatabaseInfraForm(forms.ModelForm):

    class Meta:
        model = models.DatabaseInfra


# class DatabaseInfraAddForm(forms.ModelForm):
#
#     #endpoint = forms.CharField(widget=forms.HiddenInput())
#
#     class Meta:
#         model = models.DatabaseInfra
