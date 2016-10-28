# -*- coding: utf-8 -*-
import logging
from util import full_stack
from workflow.steps.mysql.util import get_client_for_infra
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0013

LOG = logging.getLogger(__name__)


class CreateFoxHAMySQLUser(BaseStep):

    def __unicode__(self):
        return "Creating FOXHA MySQL user..."

    def do(self, workflow_dict):
        try:

            databaseinfra = workflow_dict['databaseinfra']
            client = get_client_for_infra(databaseinfra=databaseinfra)
            client.query("GRANT ALL PRIVILEGES ON *.* TO 'foxha'@'%' IDENTIFIED BY PASSWORD '*153A68439A5703E9A473D723F0C052DC74340FAC' WITH GRANT OPTION")

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0013)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        try:

            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0013)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
