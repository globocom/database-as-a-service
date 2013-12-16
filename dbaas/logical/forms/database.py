# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext_lazy as _
import logging
from django.forms import models
from django import forms
from ..models import Database, Credential, Project
from physical.models import Plan, Environment, DatabaseInfra, Engine
from account.models import Team

from .fields import AdvancedModelChoiceField

LOG = logging.getLogger(__name__)


class DatabaseForm(models.ModelForm):
    plan = AdvancedModelChoiceField(queryset=Plan.objects.filter(is_active='True'), required=False, widget=forms.RadioSelect, empty_label=None)
    engine = forms.ModelChoiceField(queryset=Engine.objects)
    environment = forms.ModelChoiceField(queryset=Environment.objects)
    
    class Meta:
        model = Database
        fields = ('name', 'description' ,'project', 'team', 'is_in_quarantine')

    def remove_fields_not_in_models(self):
        """remove fields not int models"""
        fields_to_remove = ["plan", "engine", "environment"]
        for field_name in fields_to_remove:
            if field_name in self.fields:
                del self.fields[field_name]


    def __init__(self, *args, **kwargs):

        super(DatabaseForm, self).__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance:
            LOG.debug("instance database form found! %s" % instance)
            #remove fields not in models
            self.remove_fields_not_in_models()
        else:
            self.fields['is_in_quarantine'].widget = forms.HiddenInput()

        # choices = [(user.id, user.username) for user in Team.user_objects.all()]
        # 
        # if self.instance and self.instance.pk:
        #     #now concatenate with the existing users...
        #     choices = choices + [(user.id, user.username) for user in self.instance.users.all()]
        # 
        # self.fields['users'].choices = choices

    def clean(self):
        cleaned_data = super(DatabaseForm, self).clean()

        # TODO: change model field to blank=False
        team = cleaned_data['team']
        LOG.debug("team: %s" % team)

        if not team:
            LOG.warning = "No team specified in database form"
            self._errors["team"] = self.error_class([_("Team: This field is required.")])

        # if there is an instance, that it means that we are in a edit page and therefore
        # it should return the default cleaned_data
        if self.instance and self.instance.id:
            return cleaned_data


        if not self.is_valid():
            raise forms.ValidationError(self.errors)

        if len(cleaned_data['name']) > 64:
            self._errors["name"] = self.error_class([_("Database name too long")])

        plan = cleaned_data['plan']
        environment = cleaned_data.get('environment', None)
        if not environment or environment not in plan.environments.all():
            raise forms.ValidationError(_("Invalid plan for selected environment."))

        cleaned_data['databaseinfra'] = DatabaseInfra.best_for(plan, environment)
        if not cleaned_data['databaseinfra']:
            raise forms.ValidationError(_("Sorry. I have no infra-structure to allocate this database. Try select another plan."))

        for infra in DatabaseInfra.objects.filter(environment=environment,plan=plan):
            if infra.databases.filter(name=cleaned_data['name']):
                self._errors["name"] = self.error_class([_("this name already exists in the selected environment")])
                del cleaned_data["name"]

        if 'name' in cleaned_data and cleaned_data['name'] in cleaned_data['databaseinfra'].get_driver().RESERVED_DATABASES_NAME:
            raise forms.ValidationError(_("%s is a reserved database name" % cleaned_data['name']))

        return cleaned_data

    def save(self, *args, **kwargs):
        if self.instance and self.instance.id:
            return super(DatabaseForm, self).save(*args, **kwargs)
        else:
            database = Database.provision(self.cleaned_data['name'], self.cleaned_data['plan'], self.cleaned_data['environment'])
            database.project = self.cleaned_data['project']
            database.description = self.cleaned_data['description']
            database.save()
            return database

    def save_m2m(self, *args, **kwargs):
        pass