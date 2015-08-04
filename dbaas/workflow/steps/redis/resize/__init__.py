# -*- coding: utf-8 -*-
import logging
from dbaas_cloudstack.models import HostAttr
from util import exec_remote_command
from workflow.exceptions.error_codes import DBAAS_0015
from util import full_stack
from util import build_context_script

LOG = logging.getLogger(__name__)


def run_vm_script(workflow_dict, context_dict, script):
    try:

        final_context_dict = dict(context_dict.items())

        instance = workflow_dict['instance']
        host = workflow_dict['host']
        host_csattr = HostAttr.objects.get(host=host)
        final_context_dict['HOSTADDRESS'] = instance.address
        final_context_dict['PORT'] = instance.port
        final_context_dict['DBPASSWORD'] = workflow_dict['databaseinfra'].password
        command = build_context_script(final_context_dict, script)
        output = {}
        return_code = exec_remote_command(server=host.address,
                                          username=host_csattr.vm_user,
                                          password=host_csattr.vm_password,
                                          command=command,
                                          output=output)
        if return_code:
            raise Exception("Could not run script. Output: {}".format(output))

        return True

    except Exception:
        traceback = full_stack()

        workflow_dict['exceptions']['error_codes'].append(DBAAS_0015)
        workflow_dict['exceptions']['traceback'].append(traceback)

        return False
