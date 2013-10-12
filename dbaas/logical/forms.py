# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import time
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
            # create new instance
            instance = Instance()
            instance.name = self.get_unique_instance_name()
            instance.engine = cleaned_data['engine']
            instance.plan = cleaned_data['plan']
            instance.save()
            self.cleaned_data['instance'] = instance

            # now, create a node

            # hardcode!!!
            from providers import ProviderFactory
            provider = ProviderFactory.factory()
            node = provider.create_node(instance)

            from drivers import factory_for
            driver = factory_for(instance)
            while True:
                time.sleep(10)
                try:
                    LOG.debug('Waiting for node %s...', node)
                    driver.check_status(node=node)
                    break
                except:
                    LOG.warning('Node %s not ready...', node, exc_info=True)

            node.is_active = True
            node.save()
        # else:
            # if not cleaned_data.get('instance', None):
            #     ## TODO MELHORAR ISTO
            #     print "passou"
            #     raise forms.ValidationError("You miss instance!")
        return cleaned_data

    def get_unique_instance_name(self):
        ### try diferent names if first exists, like NAME-1, NAME-2, ...
        name = self.cleaned_data['name'] # use same name as database
        i = 0
        while Instance.objects.filter(name=name).exists():
            i += 1
            name = "%s-%d" % (self.cleaned_data['name'], i)
        return name

