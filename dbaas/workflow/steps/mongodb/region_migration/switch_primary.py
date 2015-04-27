# -*- coding: utf-8 -*-
import logging
from util import full_stack
from util import exec_remote_command
from util import build_context_script
from dbaas_cloudstack.models import HostAttr as CS_HostAttr
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0020
from workflow.steps.util import test_bash_script_error
from workflow.steps.mongodb.util import build_mongodb_connect_string
from workflow.steps.mongodb.util import build_switch_primary_to_new_instances_script
from workflow.steps.mongodb.util import build_switch_primary_to_old_instances_script


LOG = logging.getLogger(__name__)


class SwitchPrimary(BaseStep):

    def __unicode__(self):
        return "Switching primary instance..."

    def do(self, workflow_dict):
        try:
            databaseinfra = workflow_dict['databaseinfra']

            connect_string = build_mongodb_connect_string(instances=workflow_dict['source_instances'],
                                                          databaseinfra=databaseinfra)
            context_dict = {
                'CONNECT_STRING': connect_string,
            }

            script = test_bash_script_error()
            script += build_switch_primary_to_new_instances_script()

            script = build_context_script(context_dict, script)
            output = {}

            host = workflow_dict['source_instances'][0].hostname
            cs_host_attr = CS_HostAttr.objects.get(host=host)

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
            databaseinfra = workflow_dict['databaseinfra']

            connect_string = build_mongodb_connect_string(instances=workflow_dict['source_instances'],
                                                          databaseinfra=databaseinfra)

            context_dict = {
                'CONNECT_STRING': connect_string,
            }

            script = test_bash_script_error()
            script += build_switch_primary_to_old_instances_script()
            script = build_context_script(context_dict, script)
            output = {}

            host = workflow_dict['source_instances'][0].hostname
            cs_host_attr = CS_HostAttr.objects.get(host=host)
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
