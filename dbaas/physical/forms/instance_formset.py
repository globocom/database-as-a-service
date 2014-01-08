# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.forms.models import BaseInlineFormSet

class InstanceModelFormSet(BaseInlineFormSet):

    def clean(self):
        super(InstanceModelFormSet, self).clean()

        for error in self.errors:
            if error:
                return

        completed = 0
        for cleaned_data in self.cleaned_data:
            # form has data and we aren't deleting it.
            if cleaned_data and not cleaned_data.get('DELETE', False):
                completed += 1

        # example custom validation across forms in the formset:
        if completed  == 0:
            raise ValidationError({'instances': _("Specify at least one valid instance")})
        # elif completed > 1:
            # raise ValidationError({'instances': _("Currently, you can have only one instance per databaseinfra")})