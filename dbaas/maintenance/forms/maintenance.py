# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext_lazy as _
import logging
from django import forms
from .. import models
from ..validators import validate_host_query


LOG = logging.getLogger(__name__)

class MaintenanceForm(forms.ModelForm):
    host_query = forms.CharField(widget=forms.Textarea,validators= [validate_host_query])
    class Meta:
        model = models.Maintenance
        fields = ( "description", "scheduled_for", "main_script", "rollback_script",
         "host_query","maximum_workers", "status", "celery_task_id",)

    def __init__(self, *args, **kwargs):
        super(MaintenanceForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(MaintenanceForm, self).clean()

        # if 'host_query' in cleaned_data:
        #     host_query = cleaned_data['host_query']
        #     if models.Maintenance.host_query_has_bad_statements(host_query=host_query):
        #         raise forms.ValidationError(_("%s is a bad query" % cleaned_data['host_query']))

        #     origindatabase = Database.objects.get(pk=cleaned_data['origin_database_id'])

        #     #for infra in DatabaseInfra.objects.filter(environment=origindatabase.environment,plan=origindatabase.plan):
        #     #    if infra.databases.filter(name=cleaned_data['database_clone']):
        #     #        self._errors["database_clone"] = self.error_class([_("this name already exists in the selected environment")])

        #     if len(cleaned_data['database_clone']) > 40:
        #         self._errors["database_clone"] = self.error_class([_("Database name too long")])

        #     dbs = origindatabase.team.databases_in_use_for(origindatabase.environment)
        #     database_alocation_limit = origindatabase.team.database_alocation_limit
        #     LOG.debug("dbs: %s | type: %s" % (dbs, type(dbs)))
        #     if (database_alocation_limit != 0 and len(dbs) >= database_alocation_limit):
        #         LOG.warning("The database alocation limit of %s has been exceeded for the team: %s => %s" % (database_alocation_limit, origindatabase.team, list(dbs)))
        #         raise forms.ValidationError([_("The database alocation limit of %s has been exceeded for the team:  %s => %s") % (database_alocation_limit, origindatabase.team, list(dbs))])

        #     driver = DriverFactory.get_driver_class(origindatabase.plan.engines[0].name)
        #     if cleaned_data['database_clone'] in driver.RESERVED_DATABASES_NAME:
        #         raise forms.ValidationError(_("%s is a reserved database name" % cleaned_data['database_clone']))

        #     if self._errors:
        #         return cleaned_data

        # return cleaned_data
