# -*- coding: utf-8 -*-
import logging
from util import full_stack
from dbaas_credentials.credential import Credential
from dbaas_credentials.models import CredentialType
from dbaas_zabbix import factory_for
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0012

LOG = logging.getLogger(__name__)


class CreateZabbix(BaseStep):

    def __unicode__(self):
        return "Registering zabbix monitoring..."

    def do(self, workflow_dict):
        zabbix_provider = None

        try:
            if 'databaseinfra' not in workflow_dict:
                return False

            databaseinfra = workflow_dict['databaseinfra']
            environment = workflow_dict['environment']
            integration = CredentialType.objects.get(type=CredentialType.ZABBIX)
            credentials = Credential.get_credentials(environment=environment,
                                                     integration=integration)
            zabbix_provider = factory_for(databaseinfra=databaseinfra, credentials=credentials)
            LOG.info("Creating zabbix monitoring for {}...".format(workflow_dict['dbtype']))
            zabbix_provider.create_basic_monitors()
            zabbix_provider.create_database_monitors()

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0012)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
        finally:
            if zabbix_provider:
                zabbix_provider.logout()

    def undo(self, workflow_dict):
        zabbix_provider = None

        try:
            if 'databaseinfra' not in workflow_dict:
                return False

            databaseinfra = workflow_dict['databaseinfra']
            environment = workflow_dict['environment']
            integration = CredentialType.objects.get(type=CredentialType.ZABBIX)
            credentials = Credential.get_credentials(environment=environment,
                                                     integration=integration)
            zabbix_provider = factory_for(databaseinfra=databaseinfra, credentials=credentials)
            LOG.info("Deleting zabbix monitoring for {}...".format(workflow_dict['dbtype']))
            zabbix_provider.delete_basic_monitors()
            zabbix_provider.delete_database_monitors()

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0012)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
        finally:
            if zabbix_provider:
                zabbix_provider.logout()
