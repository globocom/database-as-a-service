# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext_lazy as _
import logging
from django.forms import models
from django import forms
from .models import Database
from physical.models import Plan, DatabaseInfra

LOG = logging.getLogger(__name__)


class AdvancedModelChoiceIterator(models.ModelChoiceIterator):
    def choice(self, obj):
        """ I override this method to put plan object in view. I need this for
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
    plan = AdvancedModelChoiceField(queryset=Plan.objects.all(), required=False, widget=forms.RadioSelect, empty_label=None)

    class Meta:
        model = Database
        fields = ('name', 'project',)

    def clean(self):
        cleaned_data = super(DatabaseForm, self).clean()
        databaseinfra = DatabaseInfra.best_for(cleaned_data['plan'])
        if not databaseinfra:
            raise forms.ValidationError(_("Sorry. I have no infra-structure to allocate this database. Try select another plan."))
        cleaned_data['databaseinfra'] = databaseinfra
        return cleaned_data

    def save(self, *args, **kwargs):
        # cleaned_data = super(DatabaseForm, self).clean()
        database = Database()
        database.name = self.cleaned_data['name']
        database.databaseinfra = self.cleaned_data['databaseinfra']
        database.save()
        return database

    def save_m2m(self, *args, **kwargs):
        pass

