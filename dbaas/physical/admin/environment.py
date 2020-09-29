# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from dbaas_dbmonitor.models import EnvironmentAttr as EnvironmentDBMonitorAttr


class EnvironmentDBMonitorAttrInline(admin.StackedInline):
    model = EnvironmentDBMonitorAttr
    max_num = 1
    template = 'admin/physical/shared/inline_form.html'

    def has_delete_permission(self, request, obj=None):
        return False


class EnvironmentAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name", "min_of_zones", "stage", "cloud", "provisioner")
    save_on_top = True
    inlines = [EnvironmentDBMonitorAttrInline]
