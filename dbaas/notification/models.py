# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from django.db import models
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext_lazy as _
from django.utils import simplejson

from util.models import BaseModel

LOG = logging.getLogger(__name__)

class History(BaseModel):
    
    STATUS_PENDING = 0
    STATUS_RUNNING = 1
    STATUS_FINISHED = 2
    
    task_id = models.CharField(_('Task ID'), max_length=200, null=True, blank=True, editable=False)
    task_name = models.CharField(_('Task Name'), max_length=200, null=True, blank=True)
    user = models.CharField(max_length=255)
    ended_at = models.DateTimeField(verbose_name=_("Ended at"), null=True, blank=True)
    task_status = models.PositiveSmallIntegerField(_('Task Status'), default=0)
    context = models.TextField(null=True, blank=True)
    description = models.TextField(verbose_name=_("Description"), null=True, blank=True)

    def load_context_data(self):
        if self.context == '':
            self.context = '{}'
        self.context_data = simplejson.loads(self.context)
        return self.context_data