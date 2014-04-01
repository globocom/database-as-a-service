# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from integrations.storage.nfsaas.models import EnvironmentAttr


class EnvironmentAttrInline(admin.StackedInline):
    model = EnvironmentAttr
    max_num = 1
    def has_delete_permission(self, request, obj=None):
        return False

class EnvironmentAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name",)
    save_on_top = True
    inlines = [
        EnvironmentAttrInline,
    ]