# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from .. import models
from .task_history import TaskHistoryAdmin

admin.site.register(models.TaskHistory, TaskHistoryAdmin)
