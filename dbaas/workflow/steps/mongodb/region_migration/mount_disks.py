# -*- coding: utf-8 -*-
import logging
from util import full_stack
from util import check_ssh
from util import exec_remote_command
from util import build_context_script
from dbaas_cloudstack.models import HostAttr as CS_HostAttr
from dbaas_nfsaas.models import HostAttr as NFS_HostAttr
from workflow.steps.util.base import BaseStep
from workflow.steps.util import test_bash_script_error
from workflow.steps.mongodb.util import build_mount_disk_script
from workflow.exceptions.error_codes import DBAAS_0020

LOG = logging.getLogger(__name__)


class MountDisks(BaseStep):

    def __unicode__(self):
        return "Mounting disks files..."

    def do(self, workflow_dict):
        try:
            for index, instance in enumerate(workflow_dict['target_instances']):

                if instance.instance_type == instance.MONGODB_ARBITER:
                    continue

                host = instance.hostname

                LOG.info("Mounting disks on host {}".format(host))

                cs_host_attr = CS_HostAttr.objects.get(host=host)
                nfs_host_attr = NFS_HostAttr.objects.get(host=host)

                LOG.info("Cheking host ssh...")
                host_ready = check_ssh(server=host.address,
                                       username=cs_host_attr.vm_user,
                                       password=cs_host_attr.vm_password,
                                       wait=5, interval=10)

                if not host_ready:
                    raise Exception(str("Host %s is not ready..." % host))

                context_dict = {
                    'EXPORTPATH': nfs_host_attr.nfsaas_path,
                }

                script = test_bash_script_error()
                script += build_mount_disk_script()
                script = build_context_script(context_dict, script)
                LOG.info(script)
                output = {}
                return_code = exec_remote_command(server=host.address,
                                                  username=cs_host_attr.vm_user,
                                                  password=cs_host_attr.vm_password,
                                                  command=script,
                                                  output=output)
                LOG.info(output)
                if return_code != 0:
                    raise Exception(str(output))

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            LOG.info('Rollback mounting disks - nothing to do')

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
