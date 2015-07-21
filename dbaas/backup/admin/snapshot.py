# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from backup.tasks import make_databases_backup
from system.models import Configuration
import logging


LOG = logging.getLogger(__name__)


class SnapshotAdmin(admin.ModelAdmin):

    actions = None

    list_display = ("database_name", "instance", "start_at",
                    "end_at", "purge_at", "type", "status", "environment")
    search_fields = ("database_name", "instance__dns", )
    readonly_fields = ("database_name", "instance", "start_at", "end_at", "purge_at", "type",
                       "status", "snapshopt_id", "snapshot_name", "export_path", "size", "environment", "error")
    ordering = ["-start_at"]

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def get_changelist(self, request, **kwargs):
        from .views.main import ChangeList
        return ChangeList

    def backup_databases(request, id):
        make_databases_backup.delay()
        return HttpResponseRedirect(reverse('admin:notification_taskhistory_changelist'))

    def get_urls(self):
        from django.conf.urls import url
        urls = super(SnapshotAdmin, self).get_urls()
        my_urls = [
            (url(r'backup_databases/$', self.admin_site.admin_view(self.backup_databases)))]
        return my_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}

        backup_avaliable = Configuration.get_by_name_as_int(
            'backup_avaliable')

        extra_context['backup_avaliable'] = False
        if backup_avaliable:
            extra_context['backup_avaliable'] = True

        return super(SnapshotAdmin, self).changelist_view(request, extra_context=extra_context)
