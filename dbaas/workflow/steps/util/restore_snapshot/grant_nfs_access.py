# -*- coding: utf-8 -*-
import logging
from util import full_stack
from dbaas_nfsaas.provider import NfsaasProvider
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0021

LOG = logging.getLogger(__name__)


class GrantNFSAccess(BaseStep):

    def __unicode__(self):
        return "Granting nfs access..."

    def do(self, workflow_dict):
        try:

            databaseinfra = workflow_dict['databaseinfra']
            host = workflow_dict['host']
            nfsaas_export_id = workflow_dict['new_export_id']
            NfsaasProvider.grant_access(environment=databaseinfra.environment,
                                        plan=databaseinfra.plan,
                                        host=host,
                                        export_id=nfsaas_export_id)

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0021)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            databaseinfra = workflow_dict['databaseinfra']
            host = workflow_dict['host']
            nfsaas_export_id = workflow_dict['new_export_id']
            NfsaasProvider.revoke_access(environment=databaseinfra.environment,
                                         plan=databaseinfra.plan,
                                         host=host,
                                         export_id=nfsaas_export_id)

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0021)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
