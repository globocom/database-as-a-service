# -*- coding: utf-8 -*-
import logging
from util import full_stack
from util import exec_remote_command
from util import build_context_script
from dbaas_cloudstack.models import HostAttr as CS_HostAttr
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0023
from workflow.steps.util import test_bash_script_error
from workflow.steps.mongodb.util import build_disable_authentication_single_instance_script
from workflow.steps.mongodb.util import build_dump_database_script
from workflow.steps.mongodb.util import build_restart_database_script


LOG = logging.getLogger(__name__)


class PreReqChangeMongoDBStorageEngine(BaseStep):

    def __unicode__(self):
        return "Prerequisites to changing Storage engine to wiredTiger ..."

    def do(self, workflow_dict):
        try:

            instances = workflow_dict['instances']

            script = test_bash_script_error()
            script += build_disable_authentication_single_instance_script()
            script += build_restart_database_script()
            script += build_dump_database_script()

            context_dict = {
            }

            script = build_context_script(context_dict, script)
            output = {}

            host = instances[0].hostname
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

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0023)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        try:
            pass

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0023)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
