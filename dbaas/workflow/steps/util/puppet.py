from time import sleep
from base import BaseInstanceStep
from util import get_or_none_credentials_for
from dbaas_credentials.models import CredentialType
import logging

LOG = logging.getLogger(__name__)

CHECK_ATTEMPTS = 60
CHECK_SECONDS = 30


class Puppet(BaseInstanceStep):

    def __init__(self, *args, **kwargs):
        super(Puppet, self).__init__(*args, **kwargs)
        self._credential = ""

    def do(self):
        raise NotImplementedError

    def undo(self):
        pass

    @property
    def credential(self):
        if self._credential == "":
            self._credential = get_or_none_credentials_for(
                self.environment,
                CredentialType.PUPPET
            )

        return self._credential

    @property
    def is_running_bootstrap(self):
        script = "ps -ef | grep bootstrap-puppet3-loop.sh | grep -v grep | wc -l"
        output = self.host.ssh.run_script(script)

        return int(output['stdout'][0]) > 0

    @property
    def has_bootstrap_started(self):
        script = "cat /var/log/ks-post.log | wc -l"
        output = self.host.ssh.run_script(script)
        return int(output['stdout'][0]) > 0

    @property
    def puppet_code_status(self):
        script = "tail -7 /var/log/ks-post.log"
        output = self.host.ssh.run_script(
            script=script,
            retry=True
        )
        for line in output["stdout"]:
            if "puppet-setup" in line and "return code:" in line:
                return int(line.split("return code: ")[1]), output
        return -1, output


class Execute(Puppet):

    def __unicode__(self):
        return "Executing puppet-setup..."

    def do(self):
        if self.should_skip:
            return
        script = 'puppet-setup'
        self.host.ssh.run_script(script)


class ExecuteIfProblem(Execute):

    def __unicode__(self):
        return "Executing puppet-setup if problem..."

    def do(self):
        if self.should_skip:
            return
        if self.is_running_bootstrap:
            LOG.debug('ExecuteIfProblem - Bootstrap is running!')
            return

        puppet_code_status, output = self.puppet_code_status
        if puppet_code_status == 0:
            LOG.debug('ExecuteIfProblem - puppet_code_status == 0!')
            return

        LOG.debug('ExecuteIfProblem - puppet_code_status != 0!')
        super(ExecuteIfProblem, self).do()

class WaitingBeDone(Puppet):

    def __unicode__(self):
        return "Waiting puppet-setup be done..."

    def do(self):
        if self.should_skip:
            return
        for _ in range(CHECK_ATTEMPTS):
            if not self.is_running_bootstrap:
                LOG.debug('Bootstrap is not running!')
                return
            LOG.debug('Bootstrap is running!')
            sleep(CHECK_SECONDS)

        raise EnvironmentError("Puppet is running yet...")


class WaitingBeStarted(Puppet):

    def __unicode__(self):
        return "Waiting puppet-setup be starded..."

    def do(self):
        if self.should_skip:
            return
        for _ in range(CHECK_ATTEMPTS):
            if self.has_bootstrap_started:
                LOG.debug('Bootstrap has already been started!')
                return
            LOG.debug('Bootstrap has not been started yet!')
            sleep(CHECK_SECONDS)

        raise EnvironmentError("Puppet is running yet...")



class CheckStatus(Puppet):

    def __unicode__(self):
        return "Checking puppet status..."

    def do(self):
        if self.should_skip:
            return
        puppet_code_status, output = self.puppet_code_status
        if puppet_code_status != 0:
            error = "Puppet-setup returned an error on {}. Output: {}".format(
                self.host, output
            )
            raise EnvironmentError(error)
