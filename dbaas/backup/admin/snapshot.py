# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from django.conf.urls import url
from django.contrib import admin
from django.http import HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from backup.tasks import make_databases_backup
from system.models import Configuration

LOG = logging.getLogger(__name__)


class SnapshotAdmin(admin.ModelAdmin):

    actions = None
    list_filter = ("start_at", "database_name", "environment", "status")

    list_display = ("database_name", "instance", "start_at",
                    "end_at", "purge_at", "type", "status", "environment")
    search_fields = ("database_name", "instance__dns", 'volume__identifier')
    readonly_fields = (
        "database_name", "instance", "start_at", "end_at", "purge_at", "type",
        "status", "snapshopt_id", "snapshot_name", "size", "environment",
        "error", "is_automatic", "group", 'volume'
    )
    ordering = ["-start_at"]

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def get_changelist(self, request, **kwargs):
        from .views.main import ChangeList
        return ChangeList

    def backup_databases(self, request):
        if not self.is_backup_available:
            raise Http404

        make_databases_backup.delay()
        return HttpResponseRedirect(
            reverse('admin:notification_taskhistory_changelist')
        )

    def get_urls(self):
        urls = super(SnapshotAdmin, self).get_urls()

        my_urls = [
            url(
                r'backup_databases/$',
                self.admin_site.admin_view(self.backup_databases))
        ]

        return my_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['backup_available'] = self.is_backup_available
        return super(SnapshotAdmin, self).changelist_view(
            request, extra_context=extra_context
        )

    @property
    def is_backup_available(self):
        backup_available = Configuration.get_by_name_as_int('backup_available')
        return backup_available == 1
