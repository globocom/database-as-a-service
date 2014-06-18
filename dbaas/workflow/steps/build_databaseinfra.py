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
        return "Provisioning the databaseinfra"

    def do(self, workfow_dict):
        try:
            workfow_dict['names']= gen_infra_names(name= workfow_dict['name'], qt= workfow_dict['qt'])

            mysql_credentials = get_credentials_for(environment=workfow_dict['environment'], credential_type=CredentialType.MYSQL)

            databaseinfra = DatabaseInfra()
            databaseinfra.name = workfow_dict['names']['infra']
            databaseinfra.user  = mysql_credentials.user
            databaseinfra.password = mysql_credentials.password
            databaseinfra.engine = workfow_dict['plan'].engine_type.engines.all()[0]
            databaseinfra.plan = workfow_dict['plan']
            databaseinfra.environment = workfow_dict['environment']
            databaseinfra.capacity = 1
            databaseinfra.per_database_size_mbytes=0
            databaseinfra.save()

            LOG.info("DatabaseInfra created!")
            workfow_dict['databaseinfra']=databaseinfra

            return True
        except Exception,e:
            print e
            return False

    def undo(self, workfow_dict):
        if 'databaseinfra' in workfow_dict:
            workfow_dict['databaseinfra'].delete()
            return True
