# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
# from django.utils.translation import ugettext_lazy as _
import logging
from django.forms import models
from django import forms
from .models import Database
from physical.models import Engine, Plan, Instance

LOG = logging.getLogger(__name__)


class AdvancedModelChoiceIterator(models.ModelChoiceIterator):
    def choice(self, obj):
        opts = (self.field.prepare_value(obj), self.field.label_from_instance(obj), obj)
        return opts


class AdvancedModelChoiceField(models.ModelChoiceField):
    def _get_choices(self):
        if hasattr(self, '_choices'):
            return self._choices

        return AdvancedModelChoiceIterator(self)

    choices = property(_get_choices, models.ModelChoiceField._set_choices)


class DatabaseForm(models.ModelForm):
    instance = forms.ModelChoiceField(queryset=Instance.objects.all(), required=False)
    engine = forms.ModelChoiceField(queryset=Engine.objects.all(), required=False)
    plan = AdvancedModelChoiceField(queryset=Plan.objects.all(), required=False, widget=forms.RadioSelect, empty_label=None)

    class Meta:
        model = Database
        fields = ('name', 'project',)

    def clean(self):
        cleaned_data = super(DatabaseForm, self).clean()

        new_instance = self.data.get('new_instance', '')
        
        if new_instance == 'on':
            try:
                instance = Instance.provision(engine=self.cleaned_data['engine'],
                                                                    plan=self.cleaned_data['plan'],
                                                                    name=self.cleaned_data['name'])
                LOG.info("provisioned instance: %s" % instance)
                self.cleaned_data['instance'] = instance
                self.cleaned_data['plan'] = instance.plan
            except Exception, e:
                LOG.error("Erro validating inputed data: %s" % e)
                raise forms.ValidationError(e)
        # else:
            # if not cleaned_data.get('instance', None):
            #     ## TODO MELHORAR ISTO
            #     print "passou"
            #     raise forms.ValidationError("You miss instance!")
        return cleaned_data

