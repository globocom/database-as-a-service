# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext_lazy as _
import logging
from django.forms import models
from django import forms

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
