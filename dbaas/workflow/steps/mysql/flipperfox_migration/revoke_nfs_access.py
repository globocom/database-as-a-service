# -*- coding: utf-8 -*-
import logging
from util import full_stack
from workflow.steps.util.nfsaas_utils import delete_access
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0020

LOG = logging.getLogger(__name__)


class RevokeNFSAccess(BaseStep):

    def __unicode__(self):
        return "Revoking nfs access..."

    def do(self, workflow_dict):
        try:

            databaseinfra = workflow_dict['databaseinfra']
            source_host = workflow_dict['source_hosts'][0]
            disk = source_host.nfsaas_host_attributes.all()[0]
            for target_host in workflow_dict['target_hosts']:
                delete_access(environment=databaseinfra.environment,
                              export_id=disk.nfsaas_export_id,
                              host_delete=target_host)

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
