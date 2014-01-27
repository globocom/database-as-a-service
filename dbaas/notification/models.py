# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from django.db import models
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext_lazy as _

from util.models import BaseModel

LOG = logging.getLogger(__name__)

class History(BaseModel):
    
    STATUS_PENDING = 0
    STATUS_RUNNING = 1
    STATUS_FINISHED = 2
    
    task_name = models.CharField(_('Task Name'), max_length=200, null=True, blank=True)
    user = models.CharField(max_length=255)
    ended_at = models.DateTimeField(verbose_name=_("Ended at"), null=True, blank=True)
    status = models.PositiveSmallIntegerField(_('Status'), default=0)
    description = models.TextField(verbose_name=_("Description"), null=True, blank=True)
