# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
import logging

from ..models import TaskHistory
from dbaas import constants

LOG = logging.getLogger(__name__)

class TaskHistoryAdmin(admin.ModelAdmin):
    perm_add_database_infra = constants.PERM_ADD_DATABASE_INFRA
    actions = None
    list_display_basic = ["task_id", "task_name", "task_status", "arguments", "created_at", "ended_at"]
    list_display_advanced = list_display_basic + ["user"]
    #list_display = ["task_id", "task_name", "task_status", "user", "arguments", "created_at", "ended_at"]
    search_fields = ('task_id', "task_name", "task_status")
    # list_filter = ("task_status",)
    list_filter_basic = ["task_status",]
    list_filter_advanced = list_filter_basic + ["user", ]
    readonly_fields = ('created_at', 'ended_at', 'task_name', 'task_id', 'task_status', 'user', 'context', 'arguments', 'details')

    def queryset(self, request):
        qs = None

        if request.user.has_perm(self.perm_add_database_infra):
            qs = super(TaskHistoryAdmin, self).queryset(request)
            return qs
        else:
            if request.GET.get('user'):
                query_dict_copy = request.GET.copy()
                del query_dict_copy['user']
                request.GET = query_dict_copy
            qs = super(TaskHistoryAdmin, self).queryset(request)

        return qs.filter(user=request.user.username)

    def changelist_view(self, request, extra_context=None):
        if request.user.has_perm(self.perm_add_database_infra):
            self.list_display = self.list_display_advanced
            self.list_filter = self.list_filter_advanced
            self.list_display_links = ("task_id",)
        else:
            self.list_display = self.list_display_basic
            self.list_filter = self.list_filter_basic
            self.list_display_links = (None,)
        
        return super(TaskHistoryAdmin, self).changelist_view(request, extra_context=extra_context)