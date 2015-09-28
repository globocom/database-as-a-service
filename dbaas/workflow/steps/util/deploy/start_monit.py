# -*- coding: utf-8 -*-
import logging
from util import full_stack
from util import exec_remote_command
from dbaas_cloudstack.models import HostAttr as CS_HostAttr
from workflow.steps.util.base import BaseStep
from workflow.steps.util import test_bash_script_error
from workflow.steps.util import monit_script
from workflow.exceptions.error_codes import DBAAS_0002

LOG = logging.getLogger(__name__)


class StartMonit(BaseStep):

    def __unicode__(self):
        return "Starting monit..."

    def do(self, workflow_dict):
        try:
            option = 'start'
            for host in workflow_dict['hosts']:
                LOG.info("{} monit on host {}".format(option, host))
                cs_host_attr = CS_HostAttr.objects.get(host=host)

                script = test_bash_script_error()
                script += monit_script(option)

                LOG.info(script)
                output = {}
                return_code = exec_remote_command(server=host.address,
                                                  username=cs_host_attr.vm_user,
                                                  password=cs_host_attr.vm_password,
                                                  command=script,
                                                  output=output)
                LOG.info(output)
                if return_code != 0:
                    LOG.error("Error monit")
                    LOG.error(str(output))

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0002)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        return True
