# -*- coding: utf-8 -*-
import logging
from base import BaseStep
from logical.models import Database


LOG = logging.getLogger(__name__)


class BuildDatabase(BaseStep):

    def __unicode__(self):
        return "Creating logical database..."

    def do(self, workflow_dict):
        try:

            if not workflow_dict['team'] or not workflow_dict['description'] or not workflow_dict['databaseinfra']:
                return False

            LOG.info("Creating Database...")
            database = Database.provision(name= workflow_dict['name'], databaseinfra= workflow_dict['databaseinfra'])
            workflow_dict['database'] = database

            database.team = workflow_dict['team']

            if 'project' in workflow_dict:
                database.project = workflow_dict['project']

            database.description = workflow_dict['description']
            database.save()

            return True
        except Exception, e:
            print e
            return False

    def undo(self, workflow_dict):
        try:

            LOG.info("Destroying the database....")

            workflow_dict['database'].delete()

            return True
        except Exception, e:
            print e
            return False
