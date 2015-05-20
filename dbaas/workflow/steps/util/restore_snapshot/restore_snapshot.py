# -*- coding: utf-8 -*-
import logging
from util import full_stack
from dbaas_nfsaas.provider import NfsaasProvider
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0021

LOG = logging.getLogger(__name__)


class RestoreSnapshot(BaseStep):

    def __unicode__(self):
        return "Restoring Snapshot to a new volume..."

    def do(self, workflow_dict):
        try:

            databaseinfra = workflow_dict['databaseinfra']
            snapshot_id = workflow_dict['snapshot_id']
            nfsaas_export_id = workflow_dict['export_id']
            provider = NfsaasProvider()
            restore_result = provider.restore_snapshot(environment=databaseinfra.environment,
                                                       plan=databaseinfra.plan,
                                                       export_id=nfsaas_export_id,
                                                       snapshot_id=snapshot_id)

            job_result = provider.check_restore_nfsaas_job(environment=databaseinfra.environment,
                                                           job_id=restore_result['job'])

            if 'id' in job_result['result']:
                workflow_dict['new_export_id'] = job_result['result']['id']
                workflow_dict['new_export_path'] = job_result['result']['path']
            else:
                raise Exception('Error while restoring nfs snapshot')

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0021)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            if 'new_export_id' in workflow_dict:
                provider = NfsaasProvider()
                databaseinfra = workflow_dict['databaseinfra']
                nfsaas_export_id = workflow_dict['new_export_id']

                provider.drop_export(environment=databaseinfra.environment,
                                     plan=databaseinfra.plan,
                                     export_id=nfsaas_export_id)

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0021)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
