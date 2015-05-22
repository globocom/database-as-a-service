# -*- coding: utf-8 -*-
import logging
from util import full_stack
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0021
from dbaas_cloudstack.models import HostAttr as CsHostAttr
from dbaas_nfsaas.models import HostAttr as nfs_HostAttr
from util import exec_remote_command
from util import scape_nfsaas_export_path
from workflow.steps.util.restore_snapshot import update_fstab

LOG = logging.getLogger(__name__)


class UpdateFstab(BaseStep):

    def __unicode__(self):
        return "Updating volume information..."

    def do(self, workflow_dict):
        try:
            host = workflow_dict['host']
            source_export_path = scape_nfsaas_export_path(workflow_dict['export_path'])
            target_export_path = scape_nfsaas_export_path(workflow_dict['new_export_path'])
            return_code, output = update_fstab(host=host,
                                               source_export_path=source_export_path,
                                               target_export_path=target_export_path)
            if return_code != 0:
                raise Exception(str(output))

            host = workflow_dict['not_primary_hosts'][0]
            nfs_host_attr = nfs_HostAttr.objects.get(host=host, is_active=True)
            source_export_path = scape_nfsaas_export_path(nfs_host_attr.nfsaas_path)
            target_export_path = scape_nfsaas_export_path(workflow_dict['new_export_path_2'])
            return_code, output = update_fstab(host=host,
                                               source_export_path=source_export_path,
                                               target_export_path=target_export_path)
            if return_code != 0:
                raise Exception(str(output))

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0021)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            host = workflow_dict['host']
            source_export_path = scape_nfsaas_export_path(workflow_dict['new_export_path'])
            target_export_path = scape_nfsaas_export_path(workflow_dict['export_path'])
            return_code, output = update_fstab(host=host,
                                               source_export_path=source_export_path,
                                               target_export_path=target_export_path)
            if return_code != 0:
                raise Exception(str(output))

            host = workflow_dict['not_primary_hosts'][0]
            nfs_host_attr = nfs_HostAttr.objects.get(host=host, is_active=True)
            source_export_path = scape_nfsaas_export_path(workflow_dict['new_export_path_2'])
            target_export_path = scape_nfsaas_export_path(nfs_host_attr.nfsaas_path)
            return_code, output = update_fstab(host=host,
                                               source_export_path=source_export_path,
                                               target_export_path=target_export_path)
            if return_code != 0:
                raise Exception(str(output))

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0021)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
