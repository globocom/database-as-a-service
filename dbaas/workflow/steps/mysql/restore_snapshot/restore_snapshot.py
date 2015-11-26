# -*- coding: utf-8 -*-
import logging
from util import full_stack
from dbaas_nfsaas.provider import NfsaasProvider
from dbaas_nfsaas.models import HostAttr as nfs_HostAttr
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0021
from workflow.steps.util.restore_snapshot import destroy_unused_export

LOG = logging.getLogger(__name__)


class RestoreSnapshot(BaseStep):

    def __unicode__(self):
        return "Restoring Snapshot to a new volume..."

    def do(self, workflow_dict):
        try:

            workflow_dict['hosts_and_exports'] = []
            databaseinfra = workflow_dict['databaseinfra']
            snapshot_id = workflow_dict['snapshot_id']
            nfsaas_export_id = workflow_dict['export_id_snapshot']
            provider = NfsaasProvider()
            restore_result = provider.restore_snapshot(environment=databaseinfra.environment,
                                                       export_id=nfsaas_export_id,
                                                       snapshot_id=snapshot_id)

            job_result = provider.check_restore_nfsaas_job(environment=databaseinfra.environment,
                                                           job_id=restore_result['job'])

            if 'id' in job_result['result']:
                new_export_id = job_result['result']['id']
                new_export_path = job_result['result']['path']
            else:
                raise Exception('Error while restoring nfs snapshot')

            host = workflow_dict['host']
            workflow_dict['hosts_and_exports'].append({
                'host': host,
                'old_export_id': workflow_dict['export_id'],
                'old_export_path': workflow_dict['export_path'],
                'new_export_id': new_export_id,
                'new_export_path': new_export_path,
            })

            old_host_attr = nfs_HostAttr.objects.get(nfsaas_export_id=nfsaas_export_id)
            new_host_attr = nfs_HostAttr()
            new_host_attr.host = old_host_attr.host
            new_host_attr.nfsaas_export_id = new_export_id
            new_host_attr.nfsaas_path = new_export_path
            new_host_attr.is_active = False
            new_host_attr.nfsaas_team_id = old_host_attr.nfsaas_team_id
            new_host_attr.nfsaas_project_id = old_host_attr.nfsaas_project_id
            new_host_attr.nfsaas_environment_id = old_host_attr.nfsaas_environment_id
            new_host_attr.nfsaas_size_id = old_host_attr.nfsaas_size_id
            new_host_attr.save()

            restore_result = provider.restore_snapshot(environment=databaseinfra.environment,
                                                       export_id=nfsaas_export_id,
                                                       snapshot_id=snapshot_id)

            job_result = provider.check_restore_nfsaas_job(environment=databaseinfra.environment,
                                                           job_id=restore_result['job'])

            if 'id' in job_result['result']:
                new_export_id = job_result['result']['id']
                new_export_path = job_result['result']['path']
            else:
                raise Exception('Error while restoring nfs snapshot')

            host = workflow_dict['not_primary_hosts'][0]
            nfs_host_attr = nfs_HostAttr.objects.get(host=host, is_active=True)
            workflow_dict['hosts_and_exports'].append({
                'host': host,
                'old_export_id': nfs_host_attr.nfsaas_export_id,
                'old_export_path': nfs_host_attr.nfsaas_path,
                'new_export_id': new_export_id,
                'new_export_path': new_export_path,
            })

            new_host_attr = nfs_HostAttr()
            new_host_attr.host = old_host_attr.host
            new_host_attr.nfsaas_export_id = new_export_id
            new_host_attr.nfsaas_path = new_export_path
            new_host_attr.is_active = False
            new_host_attr.nfsaas_team_id = old_host_attr.nfsaas_team_id
            new_host_attr.nfsaas_project_id = old_host_attr.nfsaas_project_id
            new_host_attr.nfsaas_environment_id = old_host_attr.nfsaas_environment_id
            new_host_attr.nfsaas_size_id = old_host_attr.nfsaas_size_id
            new_host_attr.save()

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0021)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            for host_and_export in workflow_dict['hosts_and_exports']:
                destroy_unused_export(export_id=host_and_export['new_export_id'],
                                      export_path=host_and_export[
                                          'new_export_path'],
                                      host=host_and_export['host'],
                                      databaseinfra=workflow_dict['databaseinfra'])

                new_host_attr = nfs_HostAttr.objects.get(nfsaas_path=host_and_export['new_export_path'])
                new_host_attr.delete()

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0021)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
