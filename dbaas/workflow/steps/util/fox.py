from time import sleep
from dbaas_networkapi.utils import get_vip_ip_from_databaseinfra
from dbaas_foxha.dbaas_api import DatabaseAsAServiceApi
from dbaas_foxha.provider import FoxHAProvider
from dbaas_credentials.models import CredentialType
from util import get_credentials_for
from base import BaseInstanceStep


CHECK_ATTEMPTS = 20
CHECK_SECONDS = 30


class FoxHA(BaseInstanceStep):

    def __init__(self, instance):
        super(FoxHA, self).__init__(instance)
        self.mysql_fox_credentials = get_credentials_for(
            self.environment, CredentialType.MYSQL_FOXHA
        )
        self.mysql_replica_credentials = get_credentials_for(
            self.environment, CredentialType.MYSQL_REPLICA
        )
        self.foxha_credentials = get_credentials_for(
            self.environment, CredentialType.FOXHA
        )
        self.dbaas_api = DatabaseAsAServiceApi(
            self.infra, self.foxha_credentials
        )
        self.provider = FoxHAProvider(self.dbaas_api)

    def do(self):
        raise NotImplementedError

    def undo(self):
        pass


class OnlyFirstInstance(FoxHA):

    @property
    def is_valid(self):
        return self.instance == self.infra.instances.first()


class ConfigureGroup(OnlyFirstInstance):

    def __unicode__(self):
        return "Configuring FoxHA group..."

    @property
    def vip_ip(self):
        return get_vip_ip_from_databaseinfra(self.infra)

    def do(self):
        if not self.is_valid:
            return

        self.provider.add_group(
            self.infra.name, self.infra.name, self.vip_ip,
            self.mysql_fox_credentials.user,
            str(self.mysql_fox_credentials.password),
            self.mysql_replica_credentials.user,
            str(self.mysql_replica_credentials.password)
        )

    def undo(self):
        if not self.is_valid:
            return

        self.provider.delete_group(self.infra.name)


class ConfigureNode(FoxHA):

    def __unicode__(self):
        return "Configuring FoxHA node..."

    def do(self):
        mode = 'read_only'
        if self.instance == self.infra.instances.first():
            mode = 'read_write'

        self.provider.add_node(
            self.infra.name, self.instance.dns, self.instance.address,
            self.instance.port, mode, 'enabled'
        )

    def undo(self):
        self.provider.delete_node(self.infra.name, self.instance.address)


class Start(FoxHA):

    def __unicode__(self):
        return "Starting FoxHA..."

    def do(self):
        if not self.is_valid:
            return

        self.provider.start(self.infra.name)


class IsReplicationOk(FoxHA):

    def __unicode__(self):
        return "Checking FoxHA status..."

    def do(self):
        driver = self.infra.get_driver()
        for _ in range(CHECK_ATTEMPTS):
            if driver.is_replication_ok(self.instance):
                if driver.is_heartbeat_replication_ok(self.instance):
                    return

                driver.stop_slave(self.instance)
                sleep(1)
                driver.start_slave(self.instance)

            sleep(CHECK_SECONDS)

        raise EnvironmentError("Maximum number of attempts check replication")
