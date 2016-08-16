# -*- coding: utf-8 -*-
import logging
from util import full_stack
from util import exec_remote_command
from util import build_context_script
from dbaas_cloudstack.models import HostAttr as CS_HostAttr
from workflow.steps.util.base import BaseStep
from workflow.steps.util import test_bash_script_error
from workflow.steps.mysql.util import build_mysql_statsd_script
from workflow.exceptions.error_codes import DBAAS_0020

LOG = logging.getLogger(__name__)


class StartMySQLStasD(BaseStep):

    def __unicode__(self):
        return "Starting mysql-stastd..."

    def do(self, workflow_dict):
        try:
            for source_host in workflow_dict['source_hosts']:
                future_host = source_host.future_host
                hosts_option = [(source_host, 'stop'), (future_host, 'start')]
                for host, option in hosts_option:
                    LOG.info("Starting td_agent on host {}".format(host))

                    cs_host_attr = CS_HostAttr.objects.get(host=host)
                    context_dict = {}

                    script = test_bash_script_error()
                    script += build_mysql_statsd_script(option)
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
                        LOG.error("Error starting mysql_statsd")
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
                    LOG.info("Starting td_agent on host {}".format(host))

                    cs_host_attr = CS_HostAttr.objects.get(host=host)
                    context_dict = {}

                    script = test_bash_script_error()
                    script += build_mysql_statsd_script(option)
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
                        LOG.error("Error starting mysql_statsd")
                        LOG.error(str(output))


            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
