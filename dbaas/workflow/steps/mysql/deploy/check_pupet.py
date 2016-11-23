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
                    LOG.info("Check if puppet-setup is running on {} - attempt {} of {}"
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
                        LOG.info("Puppet-setup is not running on {}".format(host))
                        break

                    LOG.info("Puppet-setup is running on {}".format(host))

                    attempt += 1
                    if attempt == retries:
                        error = "Maximum number of attempts check is puppet is running on {}.".format(host)
                        LOG.error(error)
                        raise Exception(error)

                    sleep(interval)

                puppet_code_status, output = self.get_puppet_code_status(host, host_csattr)
                if puppet_code_status != 0:
                    message = "Puppet-setup returned an error on {}. Output: {}".format(host, output)
                    raise EnvironmentError(message)

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

    def get_puppet_code_status(self, host, cloudstack):
        output = {}
        LOG.info("Puppet-setup LOG info:")
        exec_remote_command(
            server=host.address,
            username=cloudstack.vm_user,
            password=cloudstack.vm_password,
            command="tail -7 /var/log/ks-post.log",
            output=output
        )

        for line in output["stdout"]:
            if "puppet-setup" in line and "return code:" in line:
                return int(line.split("return code: ")[1]), output
        return 0, output
