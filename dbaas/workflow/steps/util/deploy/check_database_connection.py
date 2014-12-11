# -*- coding: utf-8 -*-
import logging
from util import full_stack
from ...base import BaseStep
from ....exceptions.error_codes import DBAAS_0004

LOG = logging.getLogger(__name__)


class CheckDatabaseConnection(BaseStep):
    def __unicode__(self):
        return "Checking database connection..."

    def do(self, workflow_dict):
        try:
            if not 'databaseinfra' in workflow_dict:
                return False

            LOG.info("Getting driver class")
            driver = workflow_dict['databaseinfra'].get_driver()

            if workflow_dict['enginecod'] == workflow_dict['MONGODB'] and workflow_dict['qt'] > 1:
                LOG.info("Waiting 60 seconds to init mongodb replication...")
                from time import sleep

                sleep(60)

            if driver.check_status():
                LOG.info("Database is ok...")
                return True

            return False
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0004)
            workflow_dict['exceptions']['traceback'].append(traceback)

    def undo(self, workflow_dict):
        LOG.info("Nothing to do here...")
        return True
