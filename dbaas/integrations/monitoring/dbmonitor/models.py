# -*- coding: utf-8 -*-
from util.models import BaseModel
from django.db import models
from django.utils.translation import ugettext_lazy as _

class EnvironmentAttr(BaseModel):
    dbaas_environment = models.ForeignKey('physical.Environment', related_name="dbmonitor_environment_attributes")
    dbmonitor_environment = models.CharField(verbose_name=_("Environment ID"), max_length=10)
    class Meta:
    	verbose_name_plural = 'DBMonitor Custom Environment Attributes'


class DatabaseInfraAttr(BaseModel):
    dbaas_databaseinfra = models.ForeignKey('physical.DatabaseInfra', related_name="dbmonitor_databaseinfra_attributes")
    dbmonitor_databaseinfra = models.IntegerField(verbose_name=_("Database Infra ID"))
    class Meta:
    	verbose_name_plural = 'DBMonitor Database Infra'