# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
import logging


LOG = logging.getLogger(__name__)


class SnapshotAdmin(admin.ModelAdmin):

    actions = None

    list_display = ("database_name", "instance", "start_at", "end_at", "purge_at", "type", "status", "environment")
    search_fields = ("database_name", "instance__dns", )
    readonly_fields = ("database_name", "instance", "start_at", "end_at", "purge_at", "type", "status", "snapshopt_id", "snapshot_name", "export_path", "size", "environment")
    ordering = ["-start_at"]

    def has_delete_permission(self, request, obj=None):
        return False
    def has_add_permission(self, request, obj=None):
        return False

    def get_changelist(self, request, **kwargs):
        from .views.main import ChangeList
        return ChangeList
