# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import simple_audit
from util.models import BaseModel
from django.db import models, transaction
from django.utils.translation import ugettext_lazy as _


class PlanCSAttribute(BaseModel):

    serviceofferingid = models.CharField(verbose_name=_("Offering ID"),
                                         max_length=100,
                                         help_text="Cloud Stack Offering ID")
    templateid = models.CharField(verbose_name=_("Template ID"),
                                                 max_length=100,
                                                 help_text="Cloud Stack Template ID")
    zoneid = models.CharField(verbose_name=_("Zone ID"),
                               max_length=100,
                               help_text="Cloud Stack Zone ID")
    networkid = models.CharField(verbose_name=_("Network ID"),
                                 max_length=100,
                                 help_text="Cloud Stack Network ID")
    plan = models.ForeignKey('physical.Plan', related_name="plan_cs_attributes")
    userdata = models.TextField(verbose_name=_("User Data"),
                                help_text="Script to create config files")
    def __unicode__(self):
        return "Plan Cloud Stack Attributes (plan=%s)" % (self.plan)

    class Meta:
        permissions = (
            ("view_plancsattribute", "Can view plan cloud stack attributes"),
        )

simple_audit.register(PlanCSAttribute)