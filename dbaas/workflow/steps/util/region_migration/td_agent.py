# -*- coding: utf-8 -*-
import logging
from util import full_stack
from util import exec_remote_command
from util import build_context_script
from dbaas_cloudstack.models import HostAttr as CS_HostAttr
from workflow.steps.util.base import BaseStep
from workflow.steps.util import test_bash_script_error
from workflow.steps.util import build_start_td_agent_script
from workflow.exceptions.error_codes import DBAAS_0020

LOG = logging.getLogger(__name__)


class StartTDAgent(BaseStep):

    def __unicode__(self):
        return "Starting td agent..."

    def do(self, workflow_dict):
        try:
            for source_host in workflow_dict['source_hosts']:

                host = source_host.future_host

                LOG.info("Starting td_agent on host {}".format(host))

                cs_host_attr = CS_HostAttr.objects.get(host=host)
                context_dict = {}

                script = test_bash_script_error()
                script += build_start_td_agent_script()
                script = build_context_script(context_dict, script)
                LOG.info(script)
                output = {}
                return_code = exec_remote_command(server=host.address,
                                                  username=cs_host_attr.vm_user,
                                                  password=cs_host_attr.vm_password,
                                                  command=script,
                                                  output=output)
                LOG.info(output)
                if return_code != 0:
                    LOG.error("Error starting td_agent")
                    LOG.error(str(output))

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            LOG.info('Rollback starting td_agents - nothing to do')

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
