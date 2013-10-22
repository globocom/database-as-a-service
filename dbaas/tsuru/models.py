# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import simple_audit
import logging
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.dispatch import receiver
from util.models import BaseModel

LOG = logging.getLogger(__name__)

class Bind(BaseModel):

    service_name = models.CharField(verbose_name=_("Service Name"), max_length=200)
    service_hostname = models.CharField(verbose_name=_("Service Hostname"), max_length=200, null=True, blank=True)
    instance = models.ForeignKey('physical.Instance', related_name="binds", on_delete=models.PROTECT, null=True, blank=True)

    def __unicode__(self):
        return "%s" % self.service_name

simple_audit.register(Bind)