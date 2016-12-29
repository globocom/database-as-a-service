# -*- coding: utf-8 -*-
import logging
from util import full_stack
from util import exec_remote_command
from dbaas_cloudstack.models import HostAttr as CS_HostAttr
from workflow.steps.util.base import BaseStep
from workflow.steps.util import test_bash_script_error
from workflow.steps.util import td_agent_script
from workflow.steps.util import monit_script
from workflow.exceptions.error_codes import DBAAS_0020

LOG = logging.getLogger(__name__)


class StartTDAgent(BaseStep):

    def __unicode__(self):
        return "Starting td agent..."

    def do(self, workflow_dict):
        try:
            for source_host in workflow_dict['source_hosts']:
                future_host = source_host.future_host
                hosts_option = [(source_host, 'stop'), (future_host, 'start')]
                for host, option in hosts_option:
                    LOG.info("{} td_agent on host {}".format(option, host))
                    cs_host_attr = CS_HostAttr.objects.get(host=host)

                    script = test_bash_script_error()
                    script += monit_script(option)
                    script += td_agent_script(option)

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
            for source_host in workflow_dict['source_hosts']:
                future_host = source_host.future_host
                hosts_option = [(future_host, 'stop'), (source_host, 'start')]
                for host, option in hosts_option:
                    LOG.info("{} td_agent on host {}".format(option, host))
                    cs_host_attr = CS_HostAttr.objects.get(host=host)

                    script = test_bash_script_error()
                    script += monit_script(option)
                    script += td_agent_script(option)

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


class StopTDAgent(BaseStep):

    def __unicode__(self):
        return "Stopping td agent..."

    def do(self, workflow_dict):
        try:
            for source_host in workflow_dict['source_hosts']:
                future_host = source_host.future_host
                hosts_option = [(future_host, 'stop')]
                for host, option in hosts_option:
                    LOG.info("{} td_agent on host {}".format(option, host))
                    cs_host_attr = CS_HostAttr.objects.get(host=host)

                    script = test_bash_script_error()
                    script += monit_script(option)
                    script += td_agent_script(option)

                    LOG.info(script)
                    output = {}
                    return_code = exec_remote_command(server=host.address,
                                                      username=cs_host_attr.vm_user,
                                                      password=cs_host_attr.vm_password,
                                                      command=script,
                                                      output=output)
                    LOG.info(output)
                    if return_code != 0:
                        LOG.error("Error stopping td_agent")
                        LOG.error(str(output))

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):

        try:
            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
