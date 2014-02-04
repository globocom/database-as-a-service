# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
import logging

LOG = logging.getLogger(__name__)

class TaskHistoryAdmin(admin.ModelAdmin):
    actions = None
    list_display_basic = ["task_id", "task_name", "task_status", "arguments", "created_at", "ended_at"]
    list_display_advanced = list_display_basic + ["user"]
    #list_display = ["task_id", "task_name", "task_status", "user", "arguments", "created_at", "ended_at"]
    search_fields = ('task_id', "task_name", "task_status")
    list_filter = ("task_status",)
    readonly_fields = ('created_at', 'ended_at', 'task_name', 'task_id', 'task_status', 'user', 'context', 'arguments')

    def changelist_view(self, request, extra_context=None):
        # if request.user.has_perm(self.perm_manage_quarantine_database):
        #     self.list_filter = self.list_filter_advanced
        #     self.list_display = self.list_display_advanced
        # else:
        #     self.list_filter = self.list_filter_basic
        #     self.list_display = self.list_display_basic
        self.list_display = self.list_display_basic
        
        return super(TaskHistoryAdmin, self).changelist_view(request, extra_context=extra_context)