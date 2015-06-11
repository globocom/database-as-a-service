# -*- coding: utf-8 -*-
import logging
from time import sleep
from util import full_stack
from util import exec_remote_command
from util import build_context_script
from dbaas_cloudstack.models import HostAttr as CS_HostAttr
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0020
from workflow.steps.redis.util import reset_sentinel
from workflow.steps.util import test_bash_script_error
from workflow.steps.redis.util import build_start_stop_scripts
from workflow.steps.redis.util import build_stop_database_script
from workflow.steps.redis.util import build_stop_sentinel_script
from workflow.steps.redis.util import build_start_http_script

LOG = logging.getLogger(__name__)


class RemoveInstances(BaseStep):

    def __unicode__(self):
        return "Removing old instances..."

    def do(self, workflow_dict):
        try:
            databaseinfra = workflow_dict['databaseinfra']

            for index, source_host in enumerate(workflow_dict['source_hosts']):
                source_cs_host_attr = CS_HostAttr.objects.get(host=source_host)

                script = test_bash_script_error()
                script += build_start_stop_scripts()
                if index < 2:
                    script += build_stop_database_script()
                script += build_stop_sentinel_script()
                script += build_start_http_script()
                script = build_context_script({}, script)

                output = {}
                LOG.info(script)
                return_code = exec_remote_command(server=source_host.address,
                                                  username=source_cs_host_attr.vm_user,
                                                  password=source_cs_host_attr.vm_password,
                                                  command=script,
                                                  output=output)
                LOG.info(output)
                if return_code != 0:
                    raise Exception(str(output))

            for source_instance in workflow_dict['source_instances']:
                if source_instance.instance_type == source_instance.REDIS_SENTINEL:
                    target_instance = source_instance.future_instance
                    reset_sentinel(host=target_instance.hostname,
                                   sentinel_host=target_instance.address,
                                   sentinel_port=target_instance.port,
                                   service_name=databaseinfra.name)
                    sleep(30)

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
