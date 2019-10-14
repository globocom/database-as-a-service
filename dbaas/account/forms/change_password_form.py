# -*- coding:utf-8 -*-
from django import forms
from django.utils.translation import ugettext, ugettext_lazy as _
from ..backends import DbaasBackend
import ldap


class ChangePasswordForm(forms.Form):

    """
    A form that lets a user change set his/her password without entering the
    old password
    """
    error_messages = {
        'password_mismatch': _("The two password fields didn't match."),
    }
    new_password1 = forms.CharField(label=_("New password"),
                                    widget=forms.PasswordInput)
    new_password2 = forms.CharField(label=_("New password confirmation"),
                                    widget=forms.PasswordInput)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(ChangePasswordForm, self).__init__(*args, **kwargs)

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(
                    self.error_messages['password_mismatch'])
            else:
                ret = DbaasBackend.change_password(
                    self.user.username,
                    old_password=None,
                    new_password=self.cleaned_data['new_password1']
                )
                if isinstance(ret, ldap.CONSTRAINT_VIOLATION):
                    raise forms.ValidationError('Password recently used')

        return password2

    def save(self, commit=True):
        # self.user.set_password(self.cleaned_data['new_password1'])
        if commit:
            self.user.save()
        return self.user
