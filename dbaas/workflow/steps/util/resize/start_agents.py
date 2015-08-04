# -*- coding: utf-8 -*-
import logging
from util import full_stack
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0022
from dbaas_cloudstack.models import HostAttr
from util import exec_remote_command
from time import sleep

LOG = logging.getLogger(__name__)


class StartAgents(BaseStep):

    def __unicode__(self):
        return "Starting database agents..."

    def do(self, workflow_dict):
        try:
            databaseinfra = workflow_dict['databaseinfra']
            driver = databaseinfra.get_driver()
            host = workflow_dict['host']
            host_attr = HostAttr.objects.get(host=host)
            sleep(30)

            for agent in driver.get_database_agents():
                script = '/etc/init.d/{} start'.format(agent)
                output = {}
                return_code = exec_remote_command(server=host.address,
                                                  username=host_attr.vm_user,
                                                  password=host_attr.vm_password,
                                                  command=script,
                                                  output=output)
                LOG.info('Running {} - Return Code: {}. Output scrit: {}'.format(
                         script, return_code, output))

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0022)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0022)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
