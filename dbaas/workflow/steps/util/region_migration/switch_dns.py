# -*- coding: utf-8 -*-
import logging
from util import full_stack
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

            workflow_dict['objects_changed'] = []

            switch_dns_forward(databaseinfra=databaseinfra,
                               source_object_list=workflow_dict['source_hosts'],
                               ip_attribute_name='address',
                               dns_attribute_name='hostname',
                               equivalent_atribute_name='future_host',
                               workflow_dict=workflow_dict)

            switch_dns_forward(databaseinfra=databaseinfra,
                               source_object_list=workflow_dict['source_instances'],
                               ip_attribute_name='address',
                               dns_attribute_name='dns',
                               equivalent_atribute_name='future_instance',
                               workflow_dict=workflow_dict)

            switch_dns_forward(databaseinfra=databaseinfra,
                               source_object_list=workflow_dict['source_secondary_ips'],
                               ip_attribute_name='ip',
                               dns_attribute_name='dns',
                               equivalent_atribute_name='equivalent_dbinfraattr',
                               workflow_dict=workflow_dict)

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

            if 'objects_changed' in workflow_dict:
                for object_changed in workflow_dict['objects_changed']:
                    switch_dns_backward(
                        databaseinfra=databaseinfra,
                        source_object_list=[object_changed['source_object'], ],
                        ip_attribute_name=object_changed['ip_attribute_name'],
                        dns_attribute_name=object_changed['dns_attribute_name'],
                        equivalent_atribute_name=object_changed['equivalent_atribute_name'])
                return True

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
