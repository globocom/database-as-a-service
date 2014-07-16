# -*- coding: utf-8 -*-
import logging
from base import BaseStep

LOG = logging.getLogger(__name__)


class CheckDatabaseConnection(BaseStep):

    def __unicode__(self):
        return "Checking database connection..."

    def do(self, workflow_dict):
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

    def undo(self, workflow_dict):
        LOG.info("Nothing to do here...")
        return True
