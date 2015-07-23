# -*- coding: utf-8 -*-
import logging
from util import full_stack
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0021
from util import clean_unused_data

LOG = logging.getLogger(__name__)


class CleanOldVolumes(BaseStep):

    def __unicode__(self):
        return "Cleaning old data volumes..."

    def do(self, workflow_dict):
        try:
            for host_and_export in workflow_dict['hosts_and_exports']:
                clean_unused_data(export_id=host_and_export['old_export_id'],
                                  export_path=host_and_export['old_export_path'],
                                  host=host_and_export['host'],
                                  databaseinfra=workflow_dict['databaseinfra'])

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0021)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return True

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0021)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
