# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from util.models import BaseModel
from django.db import models
from django.utils.translation import ugettext_lazy as _



class IntegrationType(BaseModel):
    CLOUDSTACK = 1
    NFSAAS = 2
    
    INTEGRATION_CHOICES = (
        (CLOUDSTACK, 'Cloud Stack'),
        (NFSAAS, 'NFS as a Service'),
    )
    name = models.CharField(verbose_name=_("Offering ID"),
                                         max_length=100,
                                         help_text="Integration Name")
    type = models.IntegerField(choices=INTEGRATION_CHOICES,
                                default=0)
    
