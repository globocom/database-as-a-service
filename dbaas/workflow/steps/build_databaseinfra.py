# -*- coding: utf-8 -*-
from base import BaseStep
from util import gen_infra_names
from util import get_credentials_for
from dbaas_credentials.models import CredentialType
from physical.models import DatabaseInfra
import logging

LOG = logging.getLogger(__name__)


class BuildDatabaseInfra(BaseStep):

    def __unicode__(self):
        return "Initializing databaseinfra..."

    def do(self, workflow_dict):
        try:
            workflow_dict['names'] = gen_infra_names(
                name=workflow_dict['name'], qt=workflow_dict['qt'])

            mysql_credentials = get_credentials_for(
                environment=workflow_dict['environment'], credential_type=CredentialType.MYSQL)

            databaseinfra = DatabaseInfra()
            databaseinfra.name = workflow_dict['names']['infra']
            databaseinfra.user = mysql_credentials.user
            databaseinfra.password = mysql_credentials.password
            databaseinfra.engine = workflow_dict[
                'plan'].engine_type.engines.all()[0]
            databaseinfra.plan = workflow_dict['plan']
            databaseinfra.environment = workflow_dict['environment']
            databaseinfra.capacity = 1
            databaseinfra.per_database_size_mbytes = workflow_dict['plan'].max_db_size
            databaseinfra.save()

            LOG.info("DatabaseInfra created!")
            workflow_dict['databaseinfra'] = databaseinfra

            return True
        except Exception, e:
            print e
            return False

    def undo(self, workflow_dict):
        try:

            if 'databaseinfra' in workflow_dict:
                LOG.info("Destroying databaseinfra...")
                workflow_dict['databaseinfra'].delete()
                return True
        except Exception,e :
            print e
            return False
