from dbaas_credentials.models import CredentialType
from dbaas_foreman import get_foreman_provider
from physical.models import Vip
from workflow.steps.util.base import VipProviderClient

from util import exec_remote_command_host, get_or_none_credentials_for
from base import BaseInstanceStep


class Foreman(BaseInstanceStep):

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
        output = {}
        script = 'nslookup {}'.format(self.host.address)
        exec_remote_command_host(self.host, script, output)
        ret = ''.join(output['stdout'])
        if 'name = ' not in ret:
            return None
        return ret.split('name = ')[1].split('.\n')[0]

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
        self.vip = self.future_vip
        super(SetupDSRCMigrate, self).do()


class DeleteHost(Foreman):

    def __unicode__(self):
        return "Foreman removing host..."

    def do(self):
        if not self.is_valid:
            return
        fqdn = self.fqdn
        hostname = self.host.hostname
        reverse_ip = self.reverse_ip
        self.provider.delete_host(fqdn)
        self.provider.delete_host(hostname)
        if reverse_ip:
            if reverse_ip.split('.')[0] == hostname.split('.')[0]:
                self.provider.delete_host(reverse_ip)
