# -*- coding: utf-8 -*-
import logging
from util import full_stack
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0021
from workflow.steps.util.restore_snapshot import use_database_initialization_script

LOG = logging.getLogger(__name__)


class StopDatabase(BaseStep):

    def __unicode__(self):
        return "Stoping database..."

    def do(self, workflow_dict):
        try:
            databaseinfra = workflow_dict['databaseinfra']
            host = workflow_dict['host']

            return_code, output = use_database_initialization_script(databaseinfra=databaseinfra,
                                                                     host=host,
                                                                     option='stop')

            if return_code != 0:
                workflow_dict['is_database_stoped'] = True
                raise Exception(str(output))

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0021)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            if 'is_database_stoped' in workflow_dict:
                databaseinfra = workflow_dict['databaseinfra']
                host = workflow_dict['host']

                return_code, output = use_database_initialization_script(databaseinfra=databaseinfra,
                                                                         host=host,
                                                                         option='start')

                if return_code != 0:
                    raise Exception(str(output))

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0021)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
