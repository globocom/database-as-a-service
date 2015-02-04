# -*- coding: utf-8 -*-
import logging
import datetime
from logical.models import Database
from util import full_stack
from ..base import BaseStep
from ....exceptions.error_codes import DBAAS_0003

LOG = logging.getLogger(__name__)


class BuildDatabase(BaseStep):
    def __unicode__(self):
        return "Creating logical database..."

    def do(self, workflow_dict):
        try:

            if  'team' not in workflow_dict or \
                'description' not in workflow_dict or \
                'databaseinfra' not in workflow_dict:
                return False

            LOG.info("Creating Database...")
            database = Database.provision(name=workflow_dict['name'], databaseinfra=workflow_dict['databaseinfra'])

            LOG.info("Database %s created!" % database)

            LOG.info("Updating database team")
            database.team = workflow_dict['team']

            if 'project' in workflow_dict:
                LOG.info("Updating database project")
                database.project = workflow_dict['project']

            LOG.info("Updating database description")
            database.description = workflow_dict['description']

            database.save()
            workflow_dict['database'] = database

            driver = workflow_dict['databaseinfra'].get_driver()
            if driver.check_status():
                LOG.info("Database is ok...")
                database.status=database.ALIVE
                database.save()


            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0003)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        try:

            if not 'database' in workflow_dict:
                return False

            database = workflow_dict['database']

            if not database.is_in_quarantine:
                LOG.info("Putting Database in quarentine...")
                database.is_in_quarantine = True
                database.quarantine_dt = datetime.datetime.now().date()
                database.save()

            database.delete()
            LOG.info("Database destroyed....")

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0003)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
