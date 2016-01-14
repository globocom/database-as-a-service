# -*- coding: utf-8 -*-
import logging
from util import full_stack
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0023


LOG = logging.getLogger(__name__)


class UpdateEngine(BaseStep):

    def __unicode__(self):
        return "Updating DatabaseInfra Engine ..."

    def do(self, workflow_dict):
        try:

            databaseinfra = workflow_dict['databaseinfra']
            databaseinfra.engine = workflow_dict['target_engine']
            databaseinfra.save()

            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0023)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        try:
            pass

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0023)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
