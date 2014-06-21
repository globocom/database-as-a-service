# -*- coding: utf-8 -*-
import logging
from base import BaseStep
from dbaas_dnsapi.models import HOST as DNSAPI_HOST, INSTANCE as DNSAPI_INSTANCE, FLIPPER as DNSAPI_FLIPPER
from dbaas_dnsapi.models import PlanAttr, DatabaseInfraDNSList
from dbaas_cloudstack.models import Databaseinfraattr
#from util import get_credentials_for

LOG = logging.getLogger(__name__)

class CreateDns(BaseStep):

    def do(self, workflow_dict):
        for infra_attr in workflow_dict['databaseinfraattr']:

            if infra_attr.is_write:
                dnsname = infra_attr.name
            else:
                dnsname = infra_attr.name + 'r'

            planattr = PlanAttr.objects.get(dbaas_plan=workflow_dict['databaseinfra'].plan)
            if planattr.dnsapi_database_sufix:
                sufix = '.' + planattr.dnsapi_database_sufix
            else:
                sufix = ''

            if type == DNSAPI_HOST:
                domain = planattr.dnsapi_vm_domain
            else:
                domain = planattr.dnsapi_database_domain
                name += sufix

            databaseinfradnslist = DatabaseInfraDNSList(
                databaseinfra = workflow_dict['databaseinfra'].id,
                name = dnsname,
                domain = domain,
                ip = infra_attr.ip,
                type = type)
            databaseinfradnslist.save()

            dnsname = '%s.%s' % (name, domain)


    def undo(self, workflow_dict):
        pass
