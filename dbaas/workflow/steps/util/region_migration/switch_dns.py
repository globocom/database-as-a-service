# -*- coding: utf-8 -*-
import logging
from util import full_stack
from dbaas_dnsapi.provider import DNSAPIProvider
from workflow.steps.util.base import BaseStep
from workflow.steps.util import switch_dns_forward
from workflow.steps.util import switch_dns_backward
from workflow.exceptions.error_codes import DBAAS_0020

LOG = logging.getLogger(__name__)


class SwitchDNS(BaseStep):

    def __unicode__(self):
        return "Switching DNS..."

    def do(self, workflow_dict):
        try:
            databaseinfra = workflow_dict['databaseinfra']

            ## ver depois
            workflow_dict['dns_changed_hosts'] = []
            workflow_dict['dns_changed_instances'] = []
            workflow_dict['dns_changed_secondary_ips'] = []

            switch_dns_forward(databaseinfra=databaseinfra,
                               source_object_list=workflow_dict['source_hosts'],
                               ip_attribute_name='address',
                               dns_attribute_name='hostname',
                               equivalent_atribute_name='future_host')

            switch_dns_forward(databaseinfra=databaseinfra,
                               source_object_list=workflow_dict['source_instances'],
                               ip_attribute_name='address',
                               dns_attribute_name='dns',
                               equivalent_atribute_name='future_instance')

            switch_dns_forward(databaseinfra=databaseinfra,
                               source_object_list=workflow_dict['source_secondary_ips'],
                               ip_attribute_name='ip',
                               dns_attribute_name='dns',
                               equivalent_atribute_name='equivalent_dbinfraattr')

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:

            databaseinfra = workflow_dict['databaseinfra']

            switch_dns_backward(databaseinfra=databaseinfra,
                                source_object_list=workflow_dict['source_hosts'],
                                ip_attribute_name='address',
                                dns_attribute_name='hostname',
                                equivalent_atribute_name='future_host')

            switch_dns_backward(databaseinfra=databaseinfra,
                                source_object_list=workflow_dict['source_instances'],
                                ip_attribute_name='address',
                                dns_attribute_name='dns',
                                equivalent_atribute_name='future_instance')

            switch_dns_backward(databaseinfra=databaseinfra,
                                source_object_list=workflow_dict['source_secondary_ips'],
                                ip_attribute_name='ip',
                                dns_attribute_name='dns',
                                equivalent_atribute_name='equivalent_dbinfraattr')

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
