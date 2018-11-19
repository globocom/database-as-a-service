# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from physical.forms.environment_group import EnvironmentGroupForm


class EnvironmentGroupAdmin(admin.ModelAdmin):
    form = EnvironmentGroupForm
    save_on_top = True
    search_fields = ('name',)
    list_display = ('name', 'group_environments')
    list_filter = ("environments",)
    filter_horizontal = ("environments",)

    def group_environments(self, obj):
        return ",".join(obj.environments.values_list('name', flat=True))
