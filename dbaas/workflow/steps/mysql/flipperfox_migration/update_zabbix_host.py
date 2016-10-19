# -*- coding: utf-8 -*-
import logging
from util import full_stack
from dbaas_credentials.credential import Credential
from dbaas_credentials.models import CredentialType
from dbaas_zabbix import factory_for
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0012

LOG = logging.getLogger(__name__)


class UpdateZabbixHost(BaseStep):

    def __unicode__(self):
        return "Updating zabbix monitoring..."

    def do(self, workflow_dict):
        try:

            if 'databaseinfra' not in workflow_dict:
                return False

            databaseinfra = workflow_dict['databaseinfra']
            environment = databaseinfra.environment
            integration = CredentialType.objects.get(type=CredentialType.ZABBIX)
            credentials = Credential.get_credentials(environment=environment,
                                                     integration=integration)
            zabbix_provider = factory_for(databaseinfra=databaseinfra, credentials=credentials)
            LOG.info("Updating zabbix monitoring for {}...".format(databaseinfra))

            hosts = workflow_dict['source_hosts']
            for host in hosts:
                future_host = host.future_host
                zabbix_provider.update_host_interface(host_name=host.hostname,
                                                      ip=future_host.address)

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0012)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        try:
            if 'databaseinfra' not in workflow_dict:
                return False

            databaseinfra = workflow_dict['databaseinfra']
            environment = databaseinfra.environment
            integration = CredentialType.objects.get(type=CredentialType.ZABBIX)
            credentials = Credential.get_credentials(environment=environment,
                                                     integration=integration)
            zabbix_provider = factory_for(databaseinfra=databaseinfra, credentials=credentials)
            LOG.info("Updating zabbix monitoring for {}...".format(databaseinfra))
            hosts = workflow_dict['source_hosts']
            for host in hosts:
                zabbix_provider.update_host_interface(host_name=host.hostname,
                                                      ip=host.address)

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0012)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
