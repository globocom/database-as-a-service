# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.widgets import FilteredSelectMultiple

from ..models import Team


class TeamAdminForm(forms.ModelForm):
    users = forms.MultipleChoiceField(
        choices=[],
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

        choices = [(user.id, user.username)
                   for user in Team.user_objects.all()]

        if self.instance and self.instance.pk:
            # now concatenate with the existing users...
            choices = choices + [(user.id, user.username)
                                 for user in self.instance.users.all()]

        self.fields['users'].choices = choices
