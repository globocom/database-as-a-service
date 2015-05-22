# -*- coding: utf-8 -*-
import logging
from util import full_stack
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0021
from dbaas_cloudstack.models import HostAttr as CsHostAttr
from util import exec_remote_command
from util import scape_nfsaas_export_path

LOG = logging.getLogger(__name__)


class UpdateFstab(BaseStep):

    def __unicode__(self):
        return "Updating volume information..."

    def do(self, workflow_dict):
        try:
            host = workflow_dict['host']

            cs_host_attr = CsHostAttr.objects.get(host=host)

            source_export_path = scape_nfsaas_export_path(workflow_dict['export_path'])
            target_export_path = scape_nfsaas_export_path(workflow_dict['new_export_path'])

            command = """sed -i s/"{}"/"{}"/g /etc/fstab""".format(source_export_path,
                                                                   target_export_path)

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
            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0021)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
