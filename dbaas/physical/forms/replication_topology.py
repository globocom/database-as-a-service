from django import forms
from django.forms.widgets import SelectMultiple
#from django.forms.widgets import CheckboxSelectMultiple
from ..models import ReplicationTopology, Parameter


class ReplicationTopologyForm(forms.ModelForm):

    class Meta:
        model = ReplicationTopology

    def __init__(self, *args, **kwargs):
        super(ReplicationTopologyForm, self).__init__(*args, **kwargs)

        self.fields["parameter"].widget = SelectMultiple()
        #self.fields["parameter"].widget = CheckboxSelectMultiple()
        self.fields["parameter"].queryset = Parameter.objects.all()
        self.fields["parameter"].help_text = 'Select the parameters that can be changed in this topology'
