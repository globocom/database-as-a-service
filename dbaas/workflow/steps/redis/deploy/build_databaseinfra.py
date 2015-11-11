# -*- coding: utf-8 -*-
import logging
from util import gen_infra_names
from util import make_db_random_password
from physical.models import DatabaseInfra
from util import full_stack
from ...util.base import BaseStep
from ....exceptions.error_codes import DBAAS_0002

LOG = logging.getLogger(__name__)


class BuildDatabaseInfra(BaseStep):

    def __unicode__(self):
        return "Initializing databaseinfra..."

    def do(self, workflow_dict):
        try:
            workflow_dict['names'] = gen_infra_names(
                name=workflow_dict['name'], qt=workflow_dict['qt'])

            databaseinfra = DatabaseInfra()
            databaseinfra.name = workflow_dict['names']['infra']
            databaseinfra.user = ''
            databaseinfra.password = make_db_random_password()
            databaseinfra.engine = workflow_dict[
                'plan'].engine
            databaseinfra.plan = workflow_dict['plan']
            databaseinfra.environment = workflow_dict['environment']
            databaseinfra.capacity = 1
            databaseinfra.per_database_size_mbytes = workflow_dict[
                'plan'].max_db_size
            databaseinfra.save()

            LOG.info("DatabaseInfra created!")
            workflow_dict['databaseinfra'] = databaseinfra

            return True
        except Exception:

            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0002)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        try:

            if 'databaseinfra' in workflow_dict:
                LOG.info("Destroying databaseinfra...")
                workflow_dict['databaseinfra'].delete()
                return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0002)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
