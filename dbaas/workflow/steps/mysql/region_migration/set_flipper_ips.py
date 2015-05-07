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

LOG = logging.getLogger(__name__)


class SetFlipperIps(BaseStep):

    def __unicode__(self):
        return "Setting flipper IPs..."

    def do(self, workflow_dict):
        try:

            target_host_zero = workflow_dict['source_hosts'][0].future_host
            target_host_one = workflow_dict['source_hosts'][1].future_host
            databaseinfra = workflow_dict['databaseinfra']
            cs_host_attr = CS_HostAttr.objects.get(host=target_host_zero)

            context_dict = {
                'MASTERPAIRNAME': databaseinfra.name,
                'HOST01': target_host_zero,
                'HOST02': target_host_one,
            }

            script = test_bash_script_error()
            script += build_set_flipper_ips_script()
            script = build_context_script(context_dict, script)
            output = {}

            return_code = exec_remote_command(
                server=target_host_zero.address,
                username=cs_host_attr.vm_user,
                password=cs_host_attr.vm_password,
                command=script,
                output=output)

            LOG.info(output)
            if return_code != 0:
                raise Exception(str(output))

            databaseinfraattr = workflow_dict['source_secondary_ips'][0].equivalent_dbinfraattr
            databaseinfra = workflow_dict['databaseinfra']
            databaseinfra.endpoint = databaseinfraattr.ip + ":{}".format(3306)
            databaseinfra.save()

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
