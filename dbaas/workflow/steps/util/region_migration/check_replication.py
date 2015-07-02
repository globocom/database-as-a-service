# -*- coding: utf-8 -*-
import logging
from util import full_stack
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0020
from time import sleep
LOG = logging.getLogger(__name__)


class CheckReplication(BaseStep):

    def __unicode__(self):
        return "Checking replication..."

    def do(self, workflow_dict):
        try:
            databaseinfra = workflow_dict['databaseinfra']
            driver = databaseinfra.get_driver()

            instance = workflow_dict['source_instances'][0].future_instance

            for attempt in range(0, 21):
                LOG.info("Waiting 10s to check replication...")
                sleep(10)

                if driver.is_replication_ok(instance):
                    return True

            raise Exception('The replication is not ok')

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        return True
