# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext_lazy as _
import logging
from django.forms import models
from django import forms
from .models import Database, Credential, NoDatabaseInfraCapacity
from physical.models import Plan, Environment
from util import make_db_random_password

LOG = logging.getLogger(__name__)


class AdvancedModelChoiceIterator(models.ModelChoiceIterator):
    def choice(self, obj):
        """ I override this method to put plan object in view. I need this to
        draw plan boxes """
        opts = (self.field.prepare_value(obj), self.field.label_from_instance(obj), obj)
        return opts


class AdvancedModelChoiceField(models.ModelChoiceField):
    def _get_choices(self):
        if hasattr(self, '_choices'):
            return self._choices

        return AdvancedModelChoiceIterator(self)

    choices = property(_get_choices, models.ModelChoiceField._set_choices)


class DatabaseForm(models.ModelForm):
    plan = AdvancedModelChoiceField(queryset=Plan.objects.filter(is_active='True'), required=False, widget=forms.RadioSelect, empty_label=None)
    environment = forms.ModelChoiceField(queryset=Environment.objects)

    class Meta:
        model = Database
        fields = ('name', 'project',)

    def clean(self):
        cleaned_data = super(DatabaseForm, self).clean()
        name = cleaned_data['name']
        plan = cleaned_data['plan']
        environment = cleaned_data.get('environment', None)
        if not environment or environment not in plan.environments.all():
            raise forms.ValidationError(_("Invalid plan for selected environmnet."))
        try:
            cleaned_data['databaseinfra'] = Database.provision(name, plan, environment)
        except NoDatabaseInfraCapacity:
            raise forms.ValidationError(_("Sorry. I have no infra-structure to allocate this database. Try select another plan."))
        return cleaned_data

    def save(self, *args, **kwargs):
        # cleaned_data = super(DatabaseForm, self).clean()
        database = Database.provision(self.cleaned_data['name'], self.cleaned_data['plan'], self.cleaned_data['environment'])
        database.project = self.cleaned_data['project']
        database.save()
        return database

    def save_m2m(self, *args, **kwargs):
        pass


class CredentialForm(models.ModelForm):
    #password = forms.CharField()
    
    def __init__(self, *args, **kwargs):
        super(CredentialForm, self).__init__(*args, **kwargs)
        #instance = getattr(self, 'instance', None)
        # if instance and instanceself.pk:
        # self.fields['password'].widget.attrs['readonly'] = True
        self.fields['password'].initial = make_db_random_password()
        self.fields['password'].required = False
        self.fields['password'].widget.attrs['readonly'] = True
    
    class Meta:
        model = Credential

