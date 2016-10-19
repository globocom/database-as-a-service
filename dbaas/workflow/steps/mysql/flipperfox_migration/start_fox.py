# -*- coding: utf-8 -*-
import logging
from dbaas_foxha.dbaas_api import DatabaseAsAServiceApi
from dbaas_foxha.provider import FoxHAProvider
from dbaas_credentials.models import CredentialType
from time import sleep
from util import get_credentials_for
from util import full_stack
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0013

LOG = logging.getLogger(__name__)


class StartFox(BaseStep):

    def __unicode__(self):
        return "Starting fox..."

    def do(self, workflow_dict):
        try:

            databaseinfra = workflow_dict['databaseinfra']

            foxha_credentials = get_credentials_for(environment=databaseinfra.environment,
                                                    credential_type=CredentialType.FOXHA)
            dbaas_api = DatabaseAsAServiceApi(databaseinfra=databaseinfra,
                                              credentials=foxha_credentials)

            foxprovider = FoxHAProvider(dbaas_api=dbaas_api)

            LOG.info('Starting foxha on DatabaseInfra {}'.format(databaseinfra.name))
            foxprovider.start(group_name=databaseinfra.name)

            LOG.info("Waiting 30 seconds to start VIP")
            sleep(30)

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
            driver = databaseinfra.get_driver()

            for source_instance in workflow_dict['source_instances']:
                instance = source_instance.future_instance
                client = driver.get_client(instance)
                client.query("set global read_only='ON'")

            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0013)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
