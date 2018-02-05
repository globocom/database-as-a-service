from time import sleep
from util import exec_remote_command_host
from base import BaseInstanceStep


CHECK_ATTEMPTS = 60
CHECK_SECONDS = 20


class Puppet(BaseInstanceStep):

    def do(self):
        raise NotImplementedError

    def undo(self):
        pass

    @property
    def is_running_bootstrap(self):
        output = {}
        script = "ps -ef | grep bootstrap-puppet3-loop.sh | grep -v grep | wc -l"
        return_code = exec_remote_command_host(self.host, script, output)
        if return_code != 0:
            raise EnvironmentError(str(output))

        return int(output['stdout'][0]) > 0

    @property
    def puppet_code_status(self):
        output = {}
        script = "tail -7 /var/log/ks-post.log"
        exec_remote_command_host(self.host, script, output)
        for line in output["stdout"]:
            if "puppet-setup" in line and "return code:" in line:
                return int(line.split("return code: ")[1]), output
        return 0, output


class Execute(Puppet):

    def __unicode__(self):
        return "Executing puppet-setup..."

    def do(self):
        output = {}
        script = 'puppet-setup'
        return_code = exec_remote_command_host(self.host, script, output)
        if return_code != 0:
            raise EnvironmentError(str(output))


class ExecuteIfProblem(Execute):

    def do(self):
        if self.is_running_bootstrap:
            return

        puppet_code_status, output = self.puppet_code_status
        if puppet_code_status == 0:
            return
        
        super(ExecuteIfProblem, self).do()

class WaitingBeDone(Puppet):

    def __unicode__(self):
        return "Waiting puppet-setup be done..."

    def do(self):
        for _ in range(CHECK_ATTEMPTS):
            if not self.is_running_bootstrap:
                return
            sleep(CHECK_SECONDS)

        raise EnvironmentError("Puppet is running yet...")


class CheckStatus(Puppet):

    def __unicode__(self):
        return "Checking puppet status..."

    def do(self):
        puppet_code_status, output = self.puppet_code_status
        if puppet_code_status != 0:
            error = "Puppet-setup returned an error on {}. Output: {}".format(
                self.host, output
            )
            raise EnvironmentError(error)
