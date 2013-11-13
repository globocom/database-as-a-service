# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django import forms
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.widgets import FilteredSelectMultiple

from django.contrib.auth.models import User
from ..models import Team


# as in http://stackoverflow.com/questions/6097210/assign-user-objects-to-a-group-while-editing-group-object-in-django-admin
# the solution in the previous link is no longer being used, but it was left here for documenting purpose
class TeamAdminForm(forms.ModelForm):
    users = forms.MultipleChoiceField(
        choices=[(user.id, user.username) for user in Team.user_objects.all()],
        required=False,
        widget=FilteredSelectMultiple(
            verbose_name=_('Users'),
            is_stacked=False
        )
    )

    class Meta:
        model = Team

    def __init__(self, *args, **kwargs):
        super(TeamAdminForm, self).__init__(*args, **kwargs)
        
        if self.instance and self.instance.pk:
            choices = [(user.id, user.username) for user in Team.user_objects.all()]
            #now concatenate with the existing users...
            choices = choices + [(user.id, user.username) for user in self.instance.users.all()]
            self.fields['users'].choices = choices
