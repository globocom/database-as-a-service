# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
import logging

from ..models import TaskHistory
from dbaas import constants
from account.models import Team

LOG = logging.getLogger(__name__)


class TaskHistoryAdmin(admin.ModelAdmin):
    perm_add_database_infra = constants.PERM_ADD_DATABASE_INFRA
    actions = None
    list_display_basic = ["task_id", "friendly_task_name", "task_status", "arguments", "friendly_details", "created_at",
                          "ended_at"]
    list_display_advanced = list_display_basic + ["user"]
    search_fields = (
        'task_id', "task_name", "task_status", "user", "arguments")
    list_filter_basic = ["task_status", ]
    list_filter_advanced = list_filter_basic + ["task_name", "user", ]
    readonly_fields = ('created_at', 'ended_at', 'task_name', 'task_id', 'task_status', 'user', 'context', 'arguments',
                       'friendly_details_read', 'db_id', 'relevance')
    exclude = ('details', 'object_id', 'object_class', 'database_name')

    def friendly_task_name(self, task_history):
        if task_history.task_name:
            return "%s" % task_history.task_name.split('.')[::-1][0]
        else:
            return "N/A"

    friendly_task_name.short_description = "Task Name"

    def friendly_details(self, task_history):
        if task_history.details:
            return task_history.details.split("\n")[-1]
        else:
            return "N/A"

    friendly_details.short_description = "Current Step"

    def friendly_details_read(self, task_history):
        if task_history.details:
            return task_history.details.lstrip()

    friendly_details_read.short_description = "Details"

    def has_delete_permission(self, request, obj=None):  # note the obj=None
        return False

    def has_add_permission(self, request, obj=None):  # note the obj=None
        return False

    def has_save_permission(self, request, obj=None):  # note the obj=None
        return False

    def queryset(self, request):
        qs = None

        if request.user.has_perm(self.perm_add_database_infra):
            qs = super(TaskHistoryAdmin, self).queryset(request)
            return qs

        if request.GET.get('user'):
            query_dict_copy = request.GET.copy()
            del query_dict_copy['user']
            request.GET = query_dict_copy

        qs = super(TaskHistoryAdmin, self).queryset(request)
        same_team_users = Team.users_at_same_team(request.user)
        return qs.filter(user__in=[user.username for user in same_team_users])

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
