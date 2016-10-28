# -*- coding: utf-8 -*-
import logging
from util import full_stack
from util import exec_remote_command
from util import build_context_script
from dbaas_cloudstack.models import HostAttr as CS_HostAttr
from workflow.steps.util.base import BaseStep
from workflow.steps.util import test_bash_script_error
from workflow.exceptions.error_codes import DBAAS_0020
from workflow.steps.mysql.util import build_set_flipper_ips_script
from workflow.steps.mysql.util import build_turn_flipper_ip_down_script

LOG = logging.getLogger(__name__)


class TurnFlipperIpDown(BaseStep):

    def __unicode__(self):
        return "Setting flipper IPs..."

    def do(self, workflow_dict):
        try:

            host = workflow_dict['source_hosts'][0]
            databaseinfra = workflow_dict['databaseinfra']
            cs_host_attr = CS_HostAttr.objects.get(host=host)

            context_dict = {
                'MASTERPAIRNAME': databaseinfra.name,
            }

            script = test_bash_script_error()
            script += build_turn_flipper_ip_down_script()
            script = build_context_script(context_dict, script)
            output = {}

            return_code = exec_remote_command(
                server=host.address,
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

            source_host_zero = workflow_dict['source_hosts'][0]
            source_host_one = workflow_dict['source_hosts'][1]
            databaseinfra = workflow_dict['databaseinfra']
            cs_host_attr = CS_HostAttr.objects.get(host=source_host_zero)

            context_dict = {
                'MASTERPAIRNAME': databaseinfra.name,
                'HOST01': source_host_zero,
                'HOST02': source_host_one,
            }

            script = test_bash_script_error()
            script += build_set_flipper_ips_script()
            script = build_context_script(context_dict, script)
            output = {}

            return_code = exec_remote_command(
                server=source_host_zero.address,
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
