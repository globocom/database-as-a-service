# -*- coding: utf-8 -*-
import logging
from dbaas_nfsaas.models import HostAttr
from util import full_stack
from workflow.steps.util.base import BaseStep
from workflow.steps.util.nfsaas_utils import create_access, delete_access
from workflow.exceptions.error_codes import DBAAS_0020

LOG = logging.getLogger(__name__)


class GrantNFSAccess(BaseStep):

    def __unicode__(self):
        return "Granting nfs access..."

    def do(self, workflow_dict):
        try:
            databaseinfra = workflow_dict['databaseinfra']
            source_host = workflow_dict['source_hosts'][0]
            disk = source_host.nfsaas_host_attributes.all()[0]

            return create_access(
                environment=databaseinfra.environment,
                export_path=disk.nfsaas_path_host,
                host=source_host.future_host
            )
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            databaseinfra = workflow_dict['databaseinfra']
            source_host = workflow_dict['source_hosts'][0]
            disks = source_host.nfsaas_host_attributes.all()

            return delete_access(
                environment=databaseinfra.environment,
                export_id=disks[0].nfsaas_export_id,
                host_delete=source_host.future_host
            )
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
