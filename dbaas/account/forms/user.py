# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django import forms

LOG = logging.getLogger(__name__)


class CustomUserChangeForm(UserChangeForm):

    def __init__(self, *args, **kwargs):
        super(CustomUserChangeForm, self).__init__(*args, **kwargs)
        user_field = forms.RegexField(
            label=_("Username"), max_length=100, regex=r'^[\w.@+-]+$',
            help_text=_("Required. 100 characters or fewer. Letters, "
                        "digits and @/./+/-/_ only."),
            error_messages={
                'invalid': _("This value may contain only letters, "
                             "numbers and @/./+/-/_ characters.")
            }
        )
        self.fields['username'] = user_field


class CustomUserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        user_field = forms.RegexField(
            label=_("Username"), max_length=100, regex=r'^[\w.@+-]+$',
            help_text=_("Required. 100 characters or fewer. Letters, "
                        "digits and @/./+/-/_ only."),
            error_messages={
                'invalid': _("This value may contain only letters, "
                             "numbers and @/./+/-/_ characters.")
            }
        )
        self.fields['username'] = user_field
