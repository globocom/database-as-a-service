# -*- coding: utf-8 -*-
import logging
from util import full_stack
from dbaas_dbmonitor.provider import DBMonitorProvider
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0023


LOG = logging.getLogger(__name__)


class UpdateDBMonitorDatabasInfraVersion(BaseStep):

    def __unicode__(self):
        return "Updating DBMonitor DatabaseInfra version ..."

    def do(self, workflow_dict):
        try:

            databaseinfra = workflow_dict['databaseinfra']
            target_engine = workflow_dict['target_engine']
            DBMonitorProvider().update_dbmonitor_database_version(
                databaseinfra=databaseinfra,
                new_version=target_engine.version
            )

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
