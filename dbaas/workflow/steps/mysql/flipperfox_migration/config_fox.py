# -*- coding: utf-8 -*-
import logging
from dbaas_foxha.dbaas_api import DatabaseAsAServiceApi
from dbaas_foxha.provider import FoxHAProvider
from dbaas_credentials.models import CredentialType
from util import get_credentials_for
from util import full_stack
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0013

LOG = logging.getLogger(__name__)


class ConfigFox(BaseStep):

    def __unicode__(self):
        return "Configuring fox..."

    def do(self, workflow_dict):
        try:

            databaseinfra = workflow_dict['databaseinfra']
            vip = workflow_dict['vip']
            vip_ip = vip.vip_ip
            mysql_fox_credentials = get_credentials_for(environment=databaseinfra.environment,
                                                        credential_type=CredentialType.MYSQL_FOXHA)
            mysql_repl_credentials = get_credentials_for(environment=databaseinfra.environment,
                                                         credential_type=CredentialType.MYSQL_REPLICA)

            foxha_credentials = get_credentials_for(environment=databaseinfra.environment,
                                                    credential_type=CredentialType.FOXHA)
            dbaas_api = DatabaseAsAServiceApi(databaseinfra=databaseinfra,
                                              credentials=foxha_credentials)

            foxprovider = FoxHAProvider(dbaas_api=dbaas_api)

            LOG.info('Adding foxah group {}'.format(databaseinfra.name))
            foxprovider.add_group(group_name=databaseinfra.name,
                                  description=databaseinfra.name,
                                  vip_address=vip_ip,
                                  mysql_user=mysql_fox_credentials.user,
                                  mysql_password=str(mysql_fox_credentials.password),
                                  repl_user=mysql_repl_credentials.user,
                                  repl_password=str(mysql_repl_credentials.password))

            for index, instance in enumerate(workflow_dict['target_instances']):

                if index == 0:
                    mode = 'read_write'
                else:
                    mode = 'read_only'

                LOG.info('Adding foxah node {}'.format(instance.dns))
                foxprovider.add_node(group_name=databaseinfra.name,
                                     name=instance.dns,
                                     node_ip=instance.address,
                                     port=instance.port,
                                     mode=mode,
                                     status='enabled')

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0013)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        try:
            LOG.info("Running undo...")

            databaseinfra = workflow_dict['databaseinfra']
            foxha_credentials = get_credentials_for(environment=databaseinfra.environment,
                                                    credential_type=CredentialType.FOXHA)
            dbaas_api = DatabaseAsAServiceApi(databaseinfra=databaseinfra,
                                              credentials=foxha_credentials)
            foxprovider = FoxHAProvider(dbaas_api=dbaas_api)
            for instance in workflow_dict['target_instances']:
                LOG.info('Deleting foxah node {}'.format(instance.address))
                foxprovider.delete_node(group_name=databaseinfra.name,
                                        node_ip=instance.address)

            LOG.info('Deleting foxah group {}'.format(databaseinfra.name))
            foxprovider.delete_group(group_name=databaseinfra.name)

            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0013)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
