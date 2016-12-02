# -*- coding: utf-8 -*-
import logging
from util import full_stack
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0020
from drivers.base import ConnectionError

LOG = logging.getLogger(__name__)


class CheckInstancesStatus(BaseStep):

    def __unicode__(self):
        return "Checking instances status..."

    def do(self, workflow_dict):
        try:
            databaseinfra = workflow_dict['databaseinfra']
            driver = databaseinfra.get_driver()
            for instance in driver.get_database_instances():
                msg = "Instance({}) is down".format(instance)
                exception_msg = Exception(msg)
                try:
                    status = driver.check_status(instance)
                except ConnectionError:
                    raise exception_msg
                else:
                    if status is False:
                        raise exception_msg

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
