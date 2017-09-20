# -*- coding: utf-8 -*-
from django import forms
from ..models import Parameter
from physical.configurations import configuration_exists


class ParameterForm(forms.ModelForm):

    class Meta:
        model = Parameter

    def clean(self):
        cleaned_data = super(ParameterForm, self).clean()
        name = cleaned_data.get("name")
        engine_type = cleaned_data.get("engine_type")
        if name and engine_type:
            if not configuration_exists(engine_type.name, name):
                msg = "There is no configuration for {} on {} configuration".format(name, engine_type)
                raise forms.ValidationError(msg)

        return cleaned_data
