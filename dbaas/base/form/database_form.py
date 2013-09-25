import logging
from django.utils.translation import ugettext_lazy as _
from django import forms
from ..models import Database

log = logging.getLogger(__name__)

class DatabaseForm(forms.ModelForm):
    
    class Meta:
        model = Database
