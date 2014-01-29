# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from datetime import datetime
from django.db import models
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext_lazy as _
from django.utils import simplejson

from util.models import BaseModel

LOG = logging.getLogger(__name__)

class TaskHistory(BaseModel):
    
    STATUS_PENDING = 'PENDING'
    STATUS_RUNNING = 'RUNNING'
    STATUS_FINISHED = 'FINISHED'
    
    _STATUS = [STATUS_PENDING, STATUS_RUNNING, STATUS_FINISHED] 
    
    task_id = models.CharField(_('Task ID'), max_length=200, null=True, blank=True, editable=False)
    task_name = models.CharField(_('Task Name'), max_length=200, null=True, blank=True)
    user = models.CharField(max_length=255, null=True, blank=True)
    ended_at = models.DateTimeField(verbose_name=_("Ended at"), null=True, blank=True, editable=False)
    task_status = models.CharField(_('Task Status'), max_length=100, default=STATUS_PENDING)
    context = models.TextField(null=True, blank=True)
    description = models.TextField(verbose_name=_("Description"), null=True, blank=True)

    def load_context_data(self):
        if self.context == '':
            self.context = '{}'
        self.context_data = simplejson.loads(self.context)
        return self.context_data

    def update_status_for(self, status):
        if status not in TaskHistory._STATUS:
            raise RuntimeError("Invalid task status")
        
        self.task_status = status
        if status == TaskHistory.STATUS_FINISHED:
            self.update_ended_at()
        else:
            self.save()

    def update_ended_at(self):
        self.ended_at = datetime.now()
        self.save()

    @classmethod
    def register(cls, task_return, user=None):
        LOG.info("task id: %s | task name: %s | " % (task_return.task_id,
                                                    task_return.task_name))
        task_history = TaskHistory()
        task_history.task_id = task_return.task_id
        task_history.task_name = task_return.task_name
        if user:
            task_history.user = user.username
        task_history.save()
        
        return task_history