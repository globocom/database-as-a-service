# -*- coding: utf-8 -*-
import logging
from util import full_stack
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0022
from dbaas_cloudstack.models import HostAttr as CsHostAttr
from util import exec_remote_command

LOG = logging.getLogger(__name__)


class CopyData(BaseStep):

    def __unicode__(self):
        return "Copying data..."

    def do(self, workflow_dict):
        try:
            databaseinfra = workflow_dict['databaseinfra']
            driver = databaseinfra.get_driver()
            files_to_remove = driver.remove_deprectaed_files()
            command = files_to_remove + " && cp -rp /data/* /data2"

            for host in workflow_dict['hosts']:
                cs_host_attr = CsHostAttr.objects.get(host=host)

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

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0022)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            command = 'rm -rf /data2/*'
            for host in workflow_dict['hosts']:
                cs_host_attr = CsHostAttr.objects.get(host=host)

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

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0022)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
