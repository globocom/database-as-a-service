from dbaas_credentials.models import CredentialType
from dbaas_foreman import get_foreman_provider
from dbaas_networkapi.models import Vip
from util import exec_remote_command_host, get_credentials_for
from base import BaseInstanceStep


class Foreman(BaseInstanceStep):

    def __init__(self, instance):
        super(Foreman, self).__init__(instance)
        self.credentials = get_credentials_for(
            self.environment, CredentialType.FOREMAN
        )
        self.provider = get_foreman_provider(self.infra, self.credentials)

    @property
    def fqdn(self):
        output = {}
        script = 'hostname'
        exec_remote_command_host(self.host, script, output)
        return output['stdout'][0].strip()

    @property
    def reverse_ip(self):
        output = {}
        script = 'nslookup {}'.format(self.host.address)
        exec_remote_command_host(self.host, script, output)
        ret = output['stdout'][3]
        if 'name = ' not in ret:
            return None
        return ret.split('name = ')[1].split('.\n')[0]

    def do(self):
        raise NotImplementedError

    def undo(self):
        pass


class SetupDSRC(Foreman):

    def __unicode__(self):
        return "Foreman registering DSRC class..."

    def do(self):
        vip = Vip.objects.get(databaseinfra=self.infra)
        self.provider.setup_database_dscp(
            self.fqdn, vip.vip_ip, vip.dscp, self.instance.port
        )


class DeleteHost(Foreman):

    def __unicode__(self):
        return "Foreman removing host..."

    def do(self):
        fqdn = self.fqdn
        hostname = self.host.hostname
        reverse_ip = self.reverse_ip
        self.provider.delete_host(fqdn)
        self.provider.delete_host(hostname)
        if reverse_ip:
            if reverse_ip.split('.')[0] == hostname.split('.')[0]:
                self.provider.delete_host(reverse_ip)
