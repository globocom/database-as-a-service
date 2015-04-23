# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext_lazy as _
import logging
from django.forms import models
from django import forms
from ..models import Database
from physical.models import Plan, Environment, Engine
from dbaas_cloudstack.models import  CloudStackPack
from drivers.factory import DriverFactory
from .fields import AdvancedModelChoiceField
from django import forms
from logical.widgets.database_offering_field import DatabaseOfferingWidget

LOG = logging.getLogger(__name__)

class CloneDatabaseForm(forms.Form):
    database_clone = forms.CharField(label=u'Destination database', max_length=64, required=True)
    environment = forms.ModelChoiceField(queryset=Environment.objects, widget=forms.Select(attrs={'class':'environment'}),required='True',)
    engine = forms.CharField(widget=forms.HiddenInput(),)
    origin_database_id = forms.CharField(widget=forms.HiddenInput())
    old_plan = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):

        super(CloneDatabaseForm, self).__init__(*args, **kwargs)


        if 'initial' in kwargs:
            instance = Database.objects.get(id=kwargs['initial']['origin_database_id'])
        elif 'origin_database_id' in self.data:
            instance = Database.objects.get(id= self.data['origin_database_id'])

        if instance:
            LOG.debug("instance database form found! %s" % instance)
            self.define_engine_field(database=instance)
            self.define_available_plans(database=instance)

        self.initial['old_plan'] = instance.plan.id

    def define_engine_field(self, database):
       self.initial['engine'] = database.infra.engine.engine_type.id

    def define_available_plans(self, database):
         self.fields['plan'] = forms.ModelChoiceField(queryset= Plan.objects.filter(engine_type__name=database.infra.engine.name,
            is_active=True)
            ,widget=forms.Select(attrs={'class':'plan'}),required=True,)


    def clean(self):
        cleaned_data = super(CloneDatabaseForm, self).clean()
        if 'database_clone' in cleaned_data:

            origindatabase = Database.objects.get(pk=cleaned_data['origin_database_id'])

            #for infra in DatabaseInfra.objects.filter(environment=origindatabase.environment,plan=origindatabase.plan):
            #    if infra.databases.filter(name=cleaned_data['database_clone']):
            #        self._errors["database_clone"] = self.error_class([_("this name already exists in the selected environment")])

            if len(cleaned_data['database_clone']) > 40:
                self._errors["database_clone"] = self.error_class([_("Database name too long")])

            dbs = origindatabase.team.databases_in_use_for(origindatabase.environment)
            database_alocation_limit = origindatabase.team.database_alocation_limit
            LOG.debug("dbs: %s | type: %s" % (dbs, type(dbs)))
            if (database_alocation_limit != 0 and len(dbs) >= database_alocation_limit):
                LOG.warning("The database alocation limit of %s has been exceeded for the team: %s => %s" % (database_alocation_limit, origindatabase.team, list(dbs)))
                raise forms.ValidationError([_("The database alocation limit of %s has been exceeded for the team:  %s => %s") % (database_alocation_limit, origindatabase.team, list(dbs))])

            driver = DriverFactory.get_driver_class(origindatabase.plan.engines[0].name)
            if cleaned_data['database_clone'] in driver.RESERVED_DATABASES_NAME:
                raise forms.ValidationError(_("%s is a reserved database name" % cleaned_data['database_clone']))

            if self._errors:
                return cleaned_data

        return cleaned_data


class DatabaseForm(models.ModelForm):
    plan = AdvancedModelChoiceField(queryset=Plan.objects.filter(is_active='True'),
                                    required=False, widget=forms.RadioSelect,
                                    empty_label=None)
    engine = forms.ModelChoiceField(queryset=Engine.objects)
    environment = forms.ModelChoiceField(queryset=Environment.objects)

    class Meta:
        model = Database
        fields = ('name', 'description', 'project', 'team',
                  'is_in_quarantine',)

    def remove_fields_not_in_models(self):
        """remove fields not int models"""
        fields_to_remove = ["plan", "engine", "environment"]
        for field_name in fields_to_remove:
            if field_name in self.fields:
                del self.fields[field_name]

    @classmethod
    def setup_offering_field(cls, form, db_instance):
        form.declared_fields['offering'] = forms.CharField(
            widget=DatabaseOfferingWidget(attrs={'readonly': 'readonly',
                                                 'database': db_instance}),
            required=False, initial=db_instance.offering)

    def __init__(self, *args, **kwargs):

        super(DatabaseForm, self).__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance:
            LOG.debug("instance database form found! %s" % instance)
            # remove fields not in models
            self.remove_fields_not_in_models()

        else:
            self.fields['is_in_quarantine'].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super(DatabaseForm, self).clean()

        # if there is an instance, that means that we are in a edit page and therefore
        # it should return the default cleaned_data
        if self.instance and self.instance.id:
            return cleaned_data

        # TODO: change model field to blank=False
        if 'team' in cleaned_data:
            team = cleaned_data['team']
            LOG.debug("team: %s" % team)

            if not team:
                LOG.warning("No team specified in database form")
                self._errors["team"] = self.error_class([_("Team: This field is required.")])

        if not self.is_valid():
            raise forms.ValidationError(self.errors)

        if len(cleaned_data['name']) > 40:
            self._errors["name"] = self.error_class([_("Database name too long")])

        if 'plan' in cleaned_data:
            plan = cleaned_data.get('plan', None)
            if not plan:
                self._errors["plan"] = self.error_class([_("Plan: This field is required.")])

        if 'project' in cleaned_data:
            project = cleaned_data.get('project', None)
            if not project:
                self._errors["project"] = self.error_class([_("Project: This field is required.")])

        if 'description' in cleaned_data:
            description = cleaned_data.get('description', None)
            if not description:
                self._errors["description"] = self.error_class([_("Description: This field is required.")])

        if 'environment' in cleaned_data:
            environment = cleaned_data.get('environment', None)
            if not environment or environment not in plan.environments.all():
                raise forms.ValidationError(_("Invalid plan for selected environment."))

            #validate if the team has available resources
            dbs = team.databases_in_use_for(environment)
            database_alocation_limit = team.database_alocation_limit
            LOG.debug("dbs: %s | type: %s" % (dbs, type(dbs)))
            if (database_alocation_limit != 0 and len(dbs) >= database_alocation_limit):
                LOG.warning("The database alocation limit of %s has been exceeded for the selected team %s => %s" % (database_alocation_limit, team, list(dbs)))
                self._errors["team"] = self.error_class([_("The database alocation limit of %s has been exceeded for the selected team: %s") % (database_alocation_limit, list(dbs))])

        #for infra in DatabaseInfra.objects.filter(environment=environment,):
         #   if infra.databases.filter(name=cleaned_data['name']):
          #      self._errors["name"] = self.error_class([_("this name already exists in the selected environment")])

        driver = DriverFactory.get_driver_class(plan.engines[0].name)
        if 'name' in cleaned_data and cleaned_data['name'] in driver.RESERVED_DATABASES_NAME:
            raise forms.ValidationError(_("%s is a reserved database name" % cleaned_data['name']))

        if self._errors:
            return cleaned_data

        return cleaned_data

    def save_m2m(self, *args, **kwargs):
        pass



class ResizeDatabaseForm(forms.Form):
    database_id = forms.CharField(widget=forms.HiddenInput())
    original_offering_id = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):

        super(ResizeDatabaseForm, self).__init__(*args, **kwargs)

        if 'initial' in kwargs:
            instance = Database.objects.get(id=kwargs['initial']['database_id'])

            if instance:
                LOG.debug("instance database form found! %s" % instance)
                if instance.plan.provider == instance.plan.CLOUDSTACK:
                    LOG.debug("Cloudstack plan found!")
                    self.define_target_offering_field(database_instance= instance, origin_offer=kwargs['initial']['original_offering_id'])

    def define_target_offering_field(self, database_instance, origin_offer):
       self.fields['target_offer']= forms.ModelChoiceField(
                                        queryset=CloudStackPack.objects.filter(
                                                                                                    offering__region__environment=database_instance.environment,
                                                                                                    engine_type__name= database_instance.engine_type
                                                                                                    ).exclude(offering__serviceofferingid=origin_offer),
                                        label=u'New Offering',
                                        required=True)

    def clean(self):
        cleaned_data = super(ResizeDatabaseForm, self).clean()

        if 'target_offer' in cleaned_data:

            if cleaned_data['target_offer'].offering.serviceofferingid == cleaned_data['original_offering_id']:
               raise forms.ValidationError(_("new offering must be different from the current"))

            if self._errors:
                return cleaned_data

        return cleaned_data

class LogDatabaseForm(forms.Form):
    database_id = forms.CharField(widget=forms.HiddenInput())
    def __init__(self, *args, **kwargs):

        super(LogDatabaseForm, self).__init__(*args, **kwargs)
        if 'initial' in kwargs:
            instance = Database.objects.get(id=kwargs['initial']['database_id'])

            if instance:
                LOG.debug("instance database form found! %s" % instance)
