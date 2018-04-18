# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from django.utils.translation import ugettext_lazy as _
from django import forms
from ckeditor.widgets import CKEditorWidget
from system.models import Configuration
from .. import models

log = logging.getLogger(__name__)


class PlanForm(forms.ModelForm):
    description = forms.CharField(widget=CKEditorWidget(), required=False)
    replication_topology = forms.ModelChoiceField(
        queryset=models.ReplicationTopology.objects.all()
    )

    class Meta:
        model = models.Plan

    def clean_has_persistence(self):
        engine = self.cleaned_data['engine']
        if not engine.engine_type.is_in_memory:
            return True
        return self.cleaned_data['has_persistence']

    def clean(self):
        cleaned_data = super(PlanForm, self).clean()

        engine = cleaned_data.get("engine")
        if not engine:
            msg = _("Please select a Engine Type")
            log.warning(u"%s" % msg)
            raise forms.ValidationError(msg)

        return cleaned_data


class PlanAttrInlineFormset(forms.models.BaseInlineFormSet):

    def clean(self):
        if self.instance.is_pre_provisioned:
            return

        if not self.instance.is_ha:
            return

        if not self.is_valid():
            return

        bundles = self.cleaned_data[0].get('bundle_group')
        if not bundles:
            raise forms.ValidationError("Please select the bundle's")

