# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import simple_audit
from util.models import BaseModel
from django.db import models, transaction
from django.utils.translation import ugettext_lazy as _


class CSPlanAttr(BaseModel):

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
    plan = models.ForeignKey('physical.Plan', related_name="cs_plan_attributes")
    userdata = models.TextField(verbose_name=_("User Data"),
                                help_text="Script to create config files")
    def __unicode__(self):
        return "Cloud Stack plan Attributes (plan=%s)" % (self.plan)

    class Meta:
        permissions = (
            ("view_csplanattribute", "Can view cloud stack plan attributes"),
        )

class CSHostAttr(BaseModel):

    cs_vm_id = models.CharField(verbose_name=_("Cloud Plataform Instance id"), max_length=255, blank=True, null=True)
    host = models.ForeignKey('physical.Host', related_name="cs_host_attributes")

    def __unicode__(self):
        return "Cloud Stack host Attributes (host=%s)" % (self.host)

    class Meta:
        permissions = (
            ("view_cshostattribute", "Can view cloud stack host attributes"),
        )

simple_audit.register(CSPlanAttr)
simple_audit.register(CSHostAttr)