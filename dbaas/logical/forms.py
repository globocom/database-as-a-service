# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext_lazy as _
import logging
from django.forms import models
from django import forms
from .models import Database
from physical.models import Engine, Plan, Instance

LOG = logging.getLogger(__name__)


class DatabaseForm(models.ModelForm):
    # new_instance = forms.BooleanField(required=True)
    instance = forms.ModelChoiceField(queryset=Instance.objects, required=False)
    engine = forms.ModelChoiceField(queryset=Engine.objects, required=False)
    plan = forms.ModelChoiceField(queryset=Plan.objects, required=False)

    class Meta:
        model = Database
        fields = ('name', 'product',)

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

