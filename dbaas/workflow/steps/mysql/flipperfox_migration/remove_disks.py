# -*- coding: utf-8 -*-
import logging
from util import full_stack
from util import exec_remote_command
from dbaas_cloudstack.models import HostAttr as CsHostAttr
from workflow.steps.util.base import BaseStep
from workflow.steps.util.nfsaas_utils import delete_disk
from workflow.exceptions.error_codes import DBAAS_0020

LOG = logging.getLogger(__name__)


class RemoveDisks(BaseStep):

    def __unicode__(self):
        return "Removing disks..."

    def do(self, workflow_dict):
        try:
            for host in workflow_dict['source_hosts']:
                LOG.info("Removing database files on host %s" % host)
                host_csattr = CsHostAttr.objects.get(host=host)
                output = {}
                exec_remote_command(
                    server=host.address,
                    username=host_csattr.vm_user,
                    password=host_csattr.vm_password,
                    command="/opt/dbaas/scripts/dbaas_deletedatabasefiles.sh",
                    output=output
                )
                LOG.info(output)

                LOG.info("Removing disks on host %s" % host)
                delete_disk(
                    environment=workflow_dict['environment'], host=host
                )

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
