# -*- coding: utf-8 -*-
from util.models import BaseModel
from django.db import models
from django.utils.translation import ugettext_lazy as _

class EnvironmentAttr(BaseModel):
    dbaas_environment = models.ForeignKey('physical.Environment', related_name="nfsaas_environment_attributes")
    nfsaas_environment = models.CharField(verbose_name=_("Nfaas Environment ID"), max_length=10)

class PlanAttr(BaseModel):
    dbaas_plan = models.ForeignKey('physical.Plan', related_name="nfsaas_plan_attributes")
    nfsaas_plan = models.CharField(verbose_name=_("Nfaas Plan ID"), max_length=10)

class HostAttr(BaseModel):
    host = models.ForeignKey('physical.Host', related_name="nfsaas_host_attributes", unique=True)
    nfsaas_export_id = models.CharField(verbose_name=_("Nfaas Export ID"), max_length=10)
    nfsaas_path = models.CharField(verbose_name=_("Nfaas Path"), max_length=100)
