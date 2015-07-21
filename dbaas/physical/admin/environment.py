# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from dbaas_nfsaas.models import EnvironmentAttr
from dbaas_dbmonitor.models import EnvironmentAttr as EnvironmentDBMonitorAttr


class EnvironmentAttrInline(admin.StackedInline):
    model = EnvironmentAttr
    max_num = 1
    template = 'admin/physical/shared/inline_form.html'

    def has_delete_permission(self, request, obj=None):
        return False


class EnvironmentDBMonitorAttrInline(admin.StackedInline):
    model = EnvironmentDBMonitorAttr
    max_num = 1
    template = 'admin/physical/shared/inline_form.html'

    def has_delete_permission(self, request, obj=None):
        return False


class EnvironmentAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name",)
    save_on_top = True
    inlines = [
        EnvironmentAttrInline,
        EnvironmentDBMonitorAttrInline,
    ]
