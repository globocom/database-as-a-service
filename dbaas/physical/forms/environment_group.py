# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.forms import ModelForm, ValidationError
from django.utils.translation import ugettext_lazy
from physical.models import EnvironmentGroup


class EnvironmentGroupForm(ModelForm):

    class Meta:
        model = EnvironmentGroup

    def clean(self):
        cleaned_data = super(EnvironmentGroupForm, self).clean()

        environments = cleaned_data.get("environments")
        if not environments:
            raise ValidationError("Please select some Environment")

        for environment in environments:
            groups = environment.groups.exclude(id=self.instance.id)
            if groups:
                raise ValidationError("The {} belongs to {} group".format(
                    environment, ','.join([group.name for group in groups])
                ))



        return cleaned_data
