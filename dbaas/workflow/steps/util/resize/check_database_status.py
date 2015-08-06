# -*- coding: utf-8 -*-
import logging
from ...util.base import BaseStep

LOG = logging.getLogger(__name__)


class CheckDatabaseStatus(BaseStep):

    def __unicode__(self):
        return "Checking database status..."

    def do(self, workflow_dict):
        try:
            if 'database' not in workflow_dict:
                return False

            if 'databaseinfra' not in workflow_dict:
                workflow_dict['databaseinfra'] = workflow_dict[
                    'database'].databaseinfra

            LOG.info("Getting driver class")
            driver = workflow_dict['databaseinfra'].get_driver()
            from time import sleep

            sleep(60)

            if driver.check_status():
                LOG.info("Database is ok...")
                workflow_dict['database'].status = 1
                workflow_dict['database'].save()

            return True
        except Exception as e:
            LOG.info("Error: {}".format(e))
            pass

    def undo(self, workflow_dict):
        LOG.info("Nothing to do here...")
        return True
