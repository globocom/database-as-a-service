# -*- coding: utf-8 -*-
import logging
from dbaas_cloudstack.models import HostAttr
from util import exec_remote_command
from workflow.exceptions.error_codes import DBAAS_0015
from util import full_stack
from time import sleep
from util import build_context_script

LOG = logging.getLogger(__name__)


def run_vm_script(workflow_dict, context_dict, script, reverse=False, wait=0):
    try:
        instances_detail = workflow_dict['instances_detail']

        final_context_dict = dict(
            context_dict.items() + workflow_dict['initial_context_dict'].items())

        if reverse:
            instances_detail_final = instances_detail[::-1]
        else:
            instances_detail_final = instances_detail

        for instance_detail in instances_detail_final:
            host = instance_detail['instance'].hostname
            host_csattr = HostAttr.objects.get(host=host)
            command = build_context_script(final_context_dict, script)
            output = {}
            return_code = exec_remote_command(server=host.address,
                                              username=host_csattr.vm_user,
                                              password=host_csattr.vm_password,
                                              command=command,
                                              output=output)
            if return_code:
                raise Exception, "Could not run script. Output: {}".format(
                    output)

            sleep(wait)

        return True

    except Exception, e:
        traceback = full_stack()

        workflow_dict['exceptions']['error_codes'].append(DBAAS_0015)
        workflow_dict['exceptions']['traceback'].append(traceback)

        return False
