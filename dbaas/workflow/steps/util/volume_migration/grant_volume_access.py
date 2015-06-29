# -*- coding: utf-8 -*-
import logging
from util import full_stack
from dbaas_nfsaas.provider import NfsaasProvider
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0022

LOG = logging.getLogger(__name__)


class GrantVolumeAccess(BaseStep):

    def __unicode__(self):
        return "Granting nfs access..."

    def do(self, workflow_dict):
        try:
            databaseinfra = workflow_dict['databaseinfra']
            host = workflow_dict['host']
            volume = workflow_dict['volume']
            NfsaasProvider.grant_access(environment=databaseinfra.environment,
                                        host=host,
                                        export_id=volume.nfsaas_export_id)

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0022)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0022)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
