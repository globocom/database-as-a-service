# -*- coding: utf-8 -*-
import logging
from util import full_stack
from time import sleep
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0021
from workflow.steps.util.restore_snapshot import use_database_initialization_script

LOG = logging.getLogger(__name__)


class StartDatabase(BaseStep):

    def __unicode__(self):
        return "Starting database..."

    def do(self, workflow_dict):
        try:
            databaseinfra = workflow_dict['databaseinfra']
            host = workflow_dict['host']
            hosts = [host, ]

            if workflow_dict['not_primary_hosts'] >= 1:
                hosts.extend(workflow_dict['not_primary_hosts'])

            for host in hosts:
                return_code, output = use_database_initialization_script(databaseinfra=databaseinfra,
                                                                         host=host,
                                                                         option='start')

                if return_code != 0:
                    raise Exception(str(output))

                LOG.info('Wait 1 minute before start other instance')
                sleep(60)

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0021)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            databaseinfra = workflow_dict['databaseinfra']
            host = workflow_dict['host']
            hosts = [host, ]

            if workflow_dict['not_primary_hosts'] >= 1:
                hosts.extend(workflow_dict['not_primary_hosts'])

            for host in hosts:
                return_code, output = use_database_initialization_script(databaseinfra=databaseinfra,
                                                                         host=host,
                                                                         option='stop')

                if return_code != 0:
                    LOG.info(str(output))

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0021)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
