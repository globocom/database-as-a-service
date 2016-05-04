# -*- coding: utf-8 -*-
import logging
from util import full_stack
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0021
from workflow.steps.util.restore_snapshot import use_database_initialization_script

LOG = logging.getLogger(__name__)


class StopDatabase(BaseStep):

    def __unicode__(self):
        return "Stopping database..."

    def do(self, workflow_dict):
        try:
            databaseinfra = workflow_dict['databaseinfra']
            host = workflow_dict['host']
            hosts = [host, ]
            workflow_dict['stoped_hosts'] = []

            if len(workflow_dict['not_primary_hosts']) >= 1:
                LOG.info(
                    "SECONDARY HOSTS: {}".format(workflow_dict['not_primary_hosts']))
                hosts.extend(workflow_dict['not_primary_hosts'])

            LOG.debug("HOSTS: {}".format(hosts))
            for host in hosts:
                return_code, output = use_database_initialization_script(databaseinfra=databaseinfra,
                                                                         host=host,
                                                                         option='stop')
                if return_code != 0:
                    raise Exception(str(output))

                workflow_dict['stoped_hosts'].append(host)

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

            for host in workflow_dict['stoped_hosts']:
                return_code, output = use_database_initialization_script(databaseinfra=databaseinfra,
                                                                         host=host,
                                                                         option='start')

                if return_code != 0:
                    LOG.warn(str(output))

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0021)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
