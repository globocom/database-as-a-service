# encoding: utf-8
from util.models import BaseModel
from django.db import models
from django.utils.translation import ugettext_lazy as _

class PlanAttr(BaseModel):
    dbaas_plan = models.ForeignKey('physical.Plan', related_name="dnsapi_plan_attributes")
    dnsapi_vm_domain = models.CharField(verbose_name=_("VM Domain"), max_length=100)
    dnsapi_database_domain = models.CharField(verbose_name=_("Database Domain"), max_length=100)
    dnsapi_database_sufix = models.CharField(verbose_name=_("Database Sufix"), max_length=100, null=True, blank=True)
    
    class Meta:
    	verbose_name_plural = 'DNSAPI Custom Plan Attributes'

    def __unicode__(self):
        return "DNSAPI PlanAttr (plan=%s)" % (self.dbaas_plan)

HOST = 1
INSTANCE = 2
FLIPPER = 3
#ENDPOINT = 4 # comentar depois

DNS_TYPE_CHOICES = (
    (HOST, 'Host'),
    (INSTANCE, 'Instance'),
    (FLIPPER, 'Flipper'),
)


class DatabaseInfraDNSList(BaseModel):

    databaseinfra = models.IntegerField(verbose_name=_("Database Infra ID"))
    name = models.CharField(verbose_name=_("Name"), max_length=100)
    domain = models.CharField(verbose_name=_("Domain"), max_length=100)
    dns = models.CharField(verbose_name=_("Domain"), max_length=200, null=True)
    ip = models.CharField(verbose_name=_("IP"), max_length=100)
    type = models.IntegerField(choices=DNS_TYPE_CHOICES, default=0)
    
    