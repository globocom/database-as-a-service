# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django import forms
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.widgets import FilteredSelectMultiple

from django.contrib.auth.models import User
from ..models import Role


# as in
# http://stackoverflow.com/questions/6097210/assign-user-objects-to-a-group-while-editing-group-object-in-django-admin
class RoleAdminForm(forms.ModelForm):
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=FilteredSelectMultiple(
            verbose_name=_('Users'),
            is_stacked=False
        )
    )

    class Meta:
        model = Role

    def __init__(self, *args, **kwargs):
        super(RoleAdminForm, self).__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields['users'].initial = self.instance.user_set.all()

    def save(self, commit=True):
        role = super(RoleAdminForm, self).save(commit=commit)

        if commit:
            role.user_set = self.cleaned_data['users']
        else:
            old_save_m2m = self.save_m2m

            def new_save_m2m():
                old_save_m2m()
                role.user_set = self.cleaned_data['users']
            self.save_m2m = new_save_m2m
        return role
