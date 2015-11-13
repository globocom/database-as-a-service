# -*- coding: utf-8 -*-
import logging
from util import full_stack
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0021
from dbaas_cloudstack.models import HostAttr as CsHostAttr
from util import exec_remote_command
from time import sleep

LOG = logging.getLogger(__name__)


class UmountDataVolume(BaseStep):

    def __unicode__(self):
        return "Umounting old data..."

    def do(self, workflow_dict):
        try:
            sleep(10)
            host = workflow_dict['host']
            cs_host_attr = CsHostAttr.objects.get(host=host)
            command = 'umount /data'
            output = {}
            return_code = exec_remote_command(server=host.address,
                                              username=cs_host_attr.vm_user,
                                              password=cs_host_attr.vm_password,
                                              command=command,
                                              output=output)

            if return_code != 0:
                raise Exception(str(output))

            if len(workflow_dict['not_primary_hosts']) >= 1:
                for host in workflow_dict['not_primary_hosts']:
                    cs_host_attr = CsHostAttr.objects.get(host=host)
                    command = 'rm -rf /data/data/*'

                    output = {}
                    return_code = exec_remote_command(server=host.address,
                                                      username=cs_host_attr.vm_user,
                                                      password=cs_host_attr.vm_password,
                                                      command=command,
                                                      output=output)

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
            cs_host_attr = CsHostAttr.objects.get(host=host)
            command = 'mount /data'
            output = {}
            return_code = exec_remote_command(server=host.address,
                                              username=cs_host_attr.vm_user,
                                              password=cs_host_attr.vm_password,
                                              command=command,
                                              output=output)

            if return_code != 0:
                LOG.info(str(output))

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0021)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
