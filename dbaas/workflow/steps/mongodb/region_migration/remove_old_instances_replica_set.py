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
from workflow.steps.mongodb.util import build_remove_replica_set_members_script


LOG = logging.getLogger(__name__)


class RemoveInstancesReplicaSet(BaseStep):

    def __unicode__(self):
        return "Removing instances from Replica Set..."

    def do(self, workflow_dict):
        try:

            databaseinfra = workflow_dict['databaseinfra']
            target_instances = []

            for source_instance in workflow_dict['source_instances']:
                target_instances.append(source_instance.future_instance)

            connect_string = build_mongodb_connect_string(instances=target_instances,
                                                          databaseinfra=databaseinfra)

            context_dict = {
                'CONNECT_STRING': connect_string,
                'SECUNDARY_ONE': "{}:{}".format(workflow_dict['source_instances'][0].address, workflow_dict['source_instances'][0].port),
                'SECUNDARY_TWO': "{}:{}".format(workflow_dict['source_instances'][1].address, workflow_dict['source_instances'][1].port),
                'ARBITER': "{}:{}".format(workflow_dict['source_instances'][2].address, workflow_dict['source_instances'][2].port),
            }

            script = test_bash_script_error()
            script += build_remove_replica_set_members_script()

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

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
