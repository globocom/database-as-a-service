# -*- coding: utf-8 -*-
import logging
from time import sleep
from util import exec_remote_command_host
from util import full_stack
from time import sleep
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0013, DBAAS_0007

LOG = logging.getLogger(__name__)


class CheckPuppetIsRunning(BaseStep):

    def __unicode__(self):
        return "Checking if puppet-setup is running..."

    def do(self, workflow_dict):
        try:

            script = "ps -ef | grep bootstrap-puppet3-loop.sh | grep -v grep | wc -l"
            for host in workflow_dict['hosts']:

                LOG.info("Getting vm credentials...")

                attempt = 1
                retries = 60
                interval = 20
                sleep(interval)
                while True:
                    LOG.info("Check if puppet-setup is running on {} - attempt {} of {}"
                             .format(host, attempt, retries))
                    output = {}
                    return_code = exec_remote_command_host(
                        host, script, output
                    )
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

                puppet_code_status, output = self.get_puppet_code_status(host)
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
        return True

    def get_puppet_code_status(self, host):
        output = {}
        LOG.info("Puppet-setup LOG info:")
        exec_remote_command_host(host, "tail -7 /var/log/ks-post.log", output)

        for line in output["stdout"]:
            if "puppet-setup" in line and "return code:" in line:
                return int(line.split("return code: ")[1]), output
        return 0, output


class CheckVMName(BaseStep):

    def __unicode__(self):
        return "Checking VM hostname..."

    def do(self, workflow_dict):
        hosts_to_reboot = []
        try:
            script = "hostname | grep 'localhost.localdomain' | wc -l"
            for host in workflow_dict['hosts']:
                output = {}
                return_code = exec_remote_command_host(host, script, output)
                if return_code != 0:
                    raise Exception(str(output))

                ret_value = int(output['stdout'][0])
                if ret_value >= 1:
                    LOG.info(
                        "VM {} hostname is localhost.localdomain".format(host)
                    )
                    hosts_to_reboot.append(host)
        except Exception:
            traceback = full_stack()
            workflow_dict['exceptions']['error_codes'].append(DBAAS_0007)
            workflow_dict['exceptions']['traceback'].append(traceback)
            return False

        if not hosts_to_reboot:
            return True

        script = '/sbin/reboot -f > /dev/null 2>&1 &'
        for host in hosts_to_reboot:
            LOG.info("Rebooting {}...".format(host))
            output = {}
            try:
                exec_remote_command_host(host, script, output)
            except:
                pass

        script = 'puppet-setup'
        for host in hosts_to_reboot:
            output = {}
            for attempt in range(1, 11):
                LOG.info(
                    "Running puppet {} - Attempt {}/10...".format(host, attempt)
                )

                try:
                    return_code = exec_remote_command_host(host, script, output)
                    if return_code != 0:
                        raise EnvironmentError
                except Exception:
                    LOG.info('Could not execute puppet-setup retrying. {}'.format(output))
                    sleep(30)
                else:
                    break
            else:
                workflow_dict['exceptions']['error_codes'].append(DBAAS_0007)
                workflow_dict['exceptions']['traceback'].append(
                    'Could not execute puppet-setup in {} - {}'.format(
                        host, output
                    )
                )
                return False

        return True

    def undo(self, workflow_dict):
        return True
