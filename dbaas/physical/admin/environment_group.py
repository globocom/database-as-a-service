# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin


class EnvironmentGroupAdmin(admin.ModelAdmin):
    save_on_top = True
    search_fields = ('name',)
    list_display = ('name', 'group_environments')
    list_filter = ("environments",)

    def group_environments(self, obj):
        return ",".join(obj.environments.values_list('name', flat=True))

