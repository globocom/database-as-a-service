# -*- coding: utf-8 -*-
import logging
from base import BaseStep
from logical.models import Database
import datetime


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

            LOG.info("Database %s created!" % database)
            workflow_dict['database'] = database

            LOG.info("Updating database team")
            database.team = workflow_dict['team']

            if 'project' in workflow_dict:
                LOG.info("Updating database project")
                database.project = workflow_dict['project']

            LOG.info("Updating database description")
            database.description = workflow_dict['description']

            database.save()

            return True
        except Exception, e:
            print e
            return False

    def undo(self, workflow_dict):
        try:

            if not 'database' in workflow_dict:
                if 'databaseinfra' in workflow_dict:
                    LOG.info("Loading database into workflow_dict...")
                    workflow_dict['database'] = Database.objects.filter(databaseinfra=workflow_dict['databaseinfra'])[0]
                else:
                    return False

            if not workflow_dict['database'].is_in_quarantine:
                LOG.info("Putting Database in quarentine...")
                database = workflow_dict['database']
                database.is_in_quarantine= True
                database.quarantine_dt = datetime.datetime.now().date()
                database.save()

            LOG.info("Destroying the database....")
            database.delete()

            return True
        except Exception, e:
            print e
            return False
