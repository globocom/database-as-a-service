# -*- coding: utf-8 -*-
import logging
from util import full_stack
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0021
from workflow.steps.util.nfsaas_utils import create_access

LOG = logging.getLogger(__name__)


class GrantNFSAccess(BaseStep):

    def __unicode__(self):
        return "Granting nfs access..."

    def do(self, workflow_dict):
        try:
            databaseinfra = workflow_dict['databaseinfra']

            for host_and_export in workflow_dict['hosts_and_exports']:
                create_access(
                    environment=databaseinfra.environment,
                    export_path=host_and_export['new_export_path_host'],
                    host=host_and_export['host']
                )

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0021)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0021)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
