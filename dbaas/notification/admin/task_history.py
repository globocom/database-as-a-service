# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
import logging

class TaskHistoryAdmin(admin.ModelAdmin):
    
    list_display = ["task_id", "task_name", "task_status", "user", "arguments", "created_at", "ended_at"]
    search_fields = ('task_id', "task_name", "task_status")
    list_filter = ("task_status",)
    readonly_fields = ('created_at', 'ended_at', 'task_name', 'task_id', 'task_status', 'user', 'context', 'arguments')
