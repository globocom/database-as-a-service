# -*- coding: utf-8 -*-
import logging
from util import full_stack
from dbaas_nfsaas.models import HostAttr
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0021
from workflow.steps.util.nfsaas_utils import restore_snapshot, \
    restore_wait_for_finished, delete_export

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

            restore_job = restore_snapshot(
                environment=databaseinfra.environment,
                export_id=nfsaas_export_id, snapshot_id=snapshot_id
            )
            job_result = restore_wait_for_finished(
                environment=databaseinfra.environment,
                job_id=restore_job['job']
            )

            if 'id' in job_result:
                new_export_id = job_result['id']
                new_export_path_host = job_result['path']
                new_export_path = job_result['full_path']
            else:
                raise Exception('Error while restoring nfs snapshot')

            host = workflow_dict['host']
            disk = HostAttr.objects.get(host=host, is_active=True)
            workflow_dict['hosts_and_exports'].append({
                'host': host,
                'old_export_id': disk.nfsaas_export_id,
                'old_export_path': disk.nfsaas_path,
                'old_export_path_host': disk.nfsaas_path_host,
                'new_export_id': new_export_id,
                'new_export_path': new_export_path,
                'new_export_path_host': new_export_path_host,
            })

            old_disk = HostAttr.objects.get(nfsaas_export_id=nfsaas_export_id)
            new_disk = HostAttr()
            new_disk.host = old_disk.host
            new_disk.nfsaas_export_id = new_export_id
            new_disk.nfsaas_path = new_export_path
            new_disk.nfsaas_path_host = new_export_path_host
            new_disk.is_active = False
            new_disk.nfsaas_team_id = old_disk.nfsaas_team_id
            new_disk.nfsaas_project_id = old_disk.nfsaas_project_id
            new_disk.nfsaas_environment_id = old_disk.nfsaas_environment_id
            new_disk.nfsaas_size_id = old_disk.nfsaas_size_id
            new_disk.nfsaas_size_kb = old_disk.nfsaas_size_kb
            new_disk.save()

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
            for host_and_export in workflow_dict['hosts_and_exports']:
                disk = HostAttr.objects.get(
                    nfsaas_path=host_and_export['new_export_path']
                )
                delete_export(
                    environment=databaseinfra.environment,
                    export_path=disk.nfsaas_path_host
                )

                disk.delete()

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0021)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
