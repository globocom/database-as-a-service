# -*- coding: utf-8 -*-
import logging
from time import sleep
from util import full_stack
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0013

LOG = logging.getLogger(__name__)


class CheckReplicationFoxHA(BaseStep):

    def __unicode__(self):
        return "Checking if replication is ok..."

    def do(self, workflow_dict):
        try:

            databaseinfra = workflow_dict['databaseinfra']
            driver = databaseinfra.get_driver()

            for instance in workflow_dict['instances']:

                attempt = 1
                retries = 20
                interval = 30
                while True:

                    LOG.info("Check if replication is ok on {} - attempt {} of {}"
                             .format(instance, attempt, retries))

                    if driver.is_replication_ok(instance):
                        if driver.is_heartbeat_replication_ok(instance):
                            LOG.info("Replication is ok on {}".format(instance))
                            break
                        else:
                            LOG.info("Heartbeat replication is not ok on {}".format(instance))
                            LOG.info("Restarting slave on {}".format(instance))

                            driver.stop_slave(instance)
                            sleep(1)
                            driver.start_slave(instance)
                    else:
                        LOG.info("Replication is not ok on {}".format(instance))

                    attempt += 1
                    if attempt == retries:
                        error = "Maximum number of attempts check replication on {}.".format(instance)
                        LOG.error(error)
                        raise Exception(error)

                    sleep(interval)

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0013)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        return True
