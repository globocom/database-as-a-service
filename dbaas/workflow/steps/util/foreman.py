import subprocess

from dbaas_credentials.models import CredentialType
from dbaas_foreman import get_foreman_provider
from workflow.steps.util.vm import HostStatus

from util import exec_remote_command_host, get_or_none_credentials_for
from base import BaseInstanceStep


class Foreman(BaseInstanceStep):

    host_status = HostStatus

    def __init__(self, instance):
        super(Foreman, self).__init__(instance)
        self.credentials = get_or_none_credentials_for(
            self.environment, CredentialType.FOREMAN
        )
        self._provider = None

    @property
    def provider(self):
        if self._provider is None:
            self._provider = get_foreman_provider(self.infra, self.credentials)
        return self._provider

    @property
    def fqdn(self):
        output = {}
        script = 'hostname -f'
        exec_remote_command_host(self.host, script, output)
        return output['stdout'][0].strip()

    @property
    def reverse_ip(self):
        return subprocess.check_output(
            ("nslookup {} | grep 'name' | "
             "awk '/name = / {{print $4}}' | xargs basename -s .".format(
                self.host.address)),
            shell=True)

    def is_valid(self):
        return self.credentials is not None

    def do(self):
        raise NotImplementedError

    def undo(self):
        pass


class SetupDSRC(Foreman):

    def __unicode__(self):
        return "Foreman registering DSRC class..."

    def do(self):
        if not self.is_valid:
            return

        self.provider.setup_database_dscp(
            self.fqdn, self.vip.vip_ip, self.vip.dscp, self.instance.port
        )


class SetupDSRCMigrate(SetupDSRC):
    def do(self):
        vip = self.future_vip
        self.provider.setup_database_dscp(
            self.fqdn, vip.vip_ip, vip.dscp, self.instance.port
        )


class DeleteHost(Foreman):

    def __unicode__(self):
        return "Foreman removing host..."

    def do(self):
        if not self.is_valid:
            return
        reverse_ip = self.reverse_ip
        if self.host_status.is_up(self.host):
            fqdn = self.fqdn
        else:
            fqdn = reverse_ip
        hostname = self.host.hostname
        self.provider.delete_host(fqdn)
        self.provider.delete_host(hostname)
        if reverse_ip:
            if reverse_ip.split('.')[0] == hostname.split('.')[0]:
                self.provider.delete_host(reverse_ip)
