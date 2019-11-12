import subprocess

from dbaas_credentials.models import CredentialType
from dbaas_foreman import get_foreman_provider

from util import exec_command_on_host, get_or_none_credentials_for
from base import BaseInstanceStep
from workflow.steps.util.base import HostProviderClient
from workflow.steps.util.vm import HostStatus


class FqdnNotFoundExepition(Exception):
    pass


class Foreman(BaseInstanceStep):

    host_status = HostStatus

    def __init__(self, instance):
        super(Foreman, self).__init__(instance)
        self.credentials = get_or_none_credentials_for(
            self.environment, CredentialType.FOREMAN
        )
        self._provider = None
        self.host_prov_client = HostProviderClient(self.environment)

    @property
    def provider(self):
        if self._provider is None:
            self._provider = get_foreman_provider(self.infra, self.credentials)
        return self._provider

    @property
    def fqdn(self):
        if self.host_status.is_up(self.host):
            script = 'hostname -f'
            output, exit_code = exec_command_on_host(self.host, script)
            return output['stdout'][0].strip()
        vm_properties = self.host_prov_client.get_vm_by_host(self.host)
        if vm_properties and vm_properties.fqdn:
            return vm_properties.fqdn
        raise FqdnNotFoundExepition("Fqdn is not found")

    @property
    def reverse_ip(self):
        if self.host_status.is_up(self.host):
            return subprocess.check_output(
                ("nslookup {} | grep 'name' | "
                 "awk '/name = / {{print $4}}' | xargs basename -s .".format(
                    self.host.address)),
                shell=True)
        return self.fqdn

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
        fqdn = self.fqdn
        reverse_ip = self.reverse_ip
        hostname = self.host.hostname
        self.provider.delete_host(fqdn)
        self.provider.delete_host(hostname)
        if reverse_ip:
            if reverse_ip.split('.')[0] == hostname.split('.')[0]:
                self.provider.delete_host(reverse_ip)
