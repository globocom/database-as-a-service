# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from django.forms import models
from ..models import Credential
from util import make_db_random_password

LOG = logging.getLogger(__name__)


class CredentialForm(models.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CredentialForm, self).__init__(*args, **kwargs)

        self.fields['password'].initial = make_db_random_password()
        self.fields['password'].required = False
        self.fields['password'].widget.attrs['readonly'] = True

    class Meta:
        model = Credential
