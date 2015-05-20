# -*- coding: utf-8 -*-
import logging
from util import full_stack
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0021
from dbaas_cloudstack.models import HostAttr as CsHostAttr
from util import exec_remote_command

LOG = logging.getLogger(__name__)


class MountDataVolume(BaseStep):

    def __unicode__(self):
        return "Mounting data volume..."

    def do(self, workflow_dict):
        try:
            host = workflow_dict['host']
            databaseinfra = workflow_dict['databaseinfra']

            driver = databaseinfra.get_driver()
            files_to_remove = driver.remove_deprectaed_files()

            cs_host_attr = CsHostAttr.objects.get(host=host)
            command = "mount /data" + files_to_remove

            output = {}
            exec_remote_command(server=host.address,
                                username=cs_host_attr.vm_user,
                                password=cs_host_attr.vm_password,
                                command=command,
                                output=output)

            host = workflow_dict['not_primary_hosts'][0]
            cs_host_attr = CsHostAttr.objects.get(host=host)

            output = {}

            exec_remote_command(server=host.address,
                                username=cs_host_attr.vm_user,
                                password=cs_host_attr.vm_password,
                                command=command,
                                output=output)

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
