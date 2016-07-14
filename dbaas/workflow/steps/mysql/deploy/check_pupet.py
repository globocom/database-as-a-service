# -*- coding: utf-8 -*-
import logging
from dbaas_cloudstack.models import HostAttr as CsHostAttr
from util import exec_remote_command
from util import full_stack
from time import sleep
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0013

LOG = logging.getLogger(__name__)


class CheckPuppetIsRunning(BaseStep):

    def __unicode__(self):
        return "Checking if puppet-setup is running..."

    def do(self, workflow_dict):
        try:

            script = "ps -ef | grep bootstrap-puppet3-loop.sh | grep -v grep | wc -l"
            for host in workflow_dict['hosts']:

                LOG.info("Getting vm credentials...")
                host_csattr = CsHostAttr.objects.get(host=host)

                attempt = 1
                retries = 60
                interval = 20
                sleep(interval)
                while True:
                    LOG.info("Check if puppet-setup is runnig on {} - attempt {} of {}"
                             .format(host, attempt, retries))
                    output = {}
                    return_code = exec_remote_command(server=host.address,
                                                      username=host_csattr.vm_user,
                                                      password=host_csattr.vm_password,
                                                      command=script,
                                                      output=output)
                    if return_code != 0:
                        raise Exception(str(output))

                    ret_value = int(output['stdout'][0])
                    if ret_value == 0:
                        LOG.info("Puppet-setup is not runnig on {}".format(host))
                        break

                    LOG.info("Puppet-setup is runnig on {}".format(host))

                    attempt += 1
                    if attempt == retries:
                        error = "Maximum number of attempts check is puppet is running on {}.".format(host)
                        LOG.error(error)
                        raise Exception(error)

                    sleep(interval)

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0013)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        try:

            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0013)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
