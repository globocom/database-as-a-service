# -*- coding: utf-8 -*-
from django import forms
from django.forms.widgets import SelectMultiple
#from django.forms.widgets import CheckboxSelectMultiple
from ..models import ReplicationTopology, Parameter, DatabaseInfraParameter


class ReplicationTopologyForm(forms.ModelForm):

    class Meta:
        model = ReplicationTopology

    def __init__(self, *args, **kwargs):
        super(ReplicationTopologyForm, self).__init__(*args, **kwargs)

        self.fields["parameter"].widget = SelectMultiple()
        #self.fields["parameter"].widget = CheckboxSelectMultiple()
        self.fields["parameter"].queryset = Parameter.objects.all()
        self.fields["parameter"].help_text = 'Select the parameters that can be changed in this topology'

    def clean(self):
        cleaned_data = super(ReplicationTopologyForm, self).clean()

        if self.instance.id and 'parameter' in self.changed_data:
            form_parameters = cleaned_data.get("parameter")
            topology_parameters = Parameter.objects.filter(
                replication_topologies=self.instance
            )
            for topology_parameter in topology_parameters:
                if topology_parameter not in form_parameters:
                    parametersinfra = DatabaseInfraParameter.objects.filter(
                        parameter=topology_parameter,
                        databaseinfra__plan__replication_topology=self.instance
                    )
                    if parametersinfra:
                        parameterinfra = parametersinfra[0]
                        msg = "The parameter {} can not be deleted. It has been set in the databaseinfra {}.".format(
                            parameterinfra.parameter, parameterinfra.databaseinfra
                        )
                        raise forms.ValidationError(msg)

        return cleaned_data
