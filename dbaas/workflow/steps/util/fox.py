from time import sleep
from dbaas_foxha.dbaas_api import DatabaseAsAServiceApi
from dbaas_foxha.provider import FoxHAProvider
from dbaas_credentials.models import CredentialType
from util import get_credentials_for
from base import BaseInstanceStep
from physical.models import Vip


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

    def do(self):
        if not self.is_valid:
            return

        self.provider.add_group(
            self.infra.name, self.infra.name, self.vip.vip_ip,
            self.mysql_fox_credentials.user,
            str(self.mysql_fox_credentials.password),
            self.mysql_replica_credentials.user,
            str(self.mysql_replica_credentials.password)
        )

    def undo(self):
        if not self.is_valid:
            return

        self.provider.delete_group(self.infra.name)


class RemoveGroupMigrate(ConfigureGroup):

    @property
    def is_valid(self):
        return self.instance == self.infra.instances.last()

    def __unicode__(self):
        return "Removing old Vip from FoxHA group..."

    def do(self):
        return super(RemoveGroupMigrate, self).undo()


class ConfigureGroupMigrate(ConfigureGroup):
    def __unicode__(self):
        return "Adding new Vip FoxHA group..."

    def do(self):
        self.vip = self.future_vip
        return super(ConfigureGroupMigrate, self).do()

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


class RemoveNodeMigrate(FoxHA):

    def __unicode__(self):
        return "Removing FoxHA node {}...".format(self.instance.address)

    def do(self):
        self.provider.delete_node(self.infra.name, self.host_migrate.host.address)

    def undo(self):
        mode = 'read_only'

        self.provider.add_node(
            self.infra.name, self.instance.dns, self.host_migrate.host.address,
            self.instance.port, mode, 'enabled'
        )


class ConfigureNodeMigrate(ConfigureNode):

    def __unicode__(self):
        return "Changing FoxHA node..."

    @property
    def is_master(self):
        return False

    @property
    def mode(self):
        if self.is_master:
            return 'read_write'
        return 'read_only'

    def do(self):

        self.provider.add_node(
            self.infra.name, self.instance.dns, self.host.address,
            self.instance.port, self.mode, 'enabled'
        )

    def undo(self):
        self.provider.delete_node(self.infra.name, self.host.address)


class ConfigureNodeDatabaseMigrate(ConfigureNodeMigrate):
    @property
    def is_master(self):
        return self.instance == self.infra.instances.last()


class Start(FoxHA):

    def __unicode__(self):
        return "Starting FoxHA..."

    def do(self):
        if not self.is_valid:
            return

        self.provider.start(self.infra.name)


class IsReplicationOk(FoxHA):

    def __init__(self, *args, **kw):
        super(IsReplicationOk, self).__init__(*args, **kw)
        self.verify_heartbeat = True

    def __unicode__(self):
        return "Checking FoxHA status..."

    def do(self):
        driver = self.infra.get_driver()
        if self.host_migrate and self.instance.hostname.future_host:
            self.instance.address = self.instance.hostname.future_host.address
        for _ in range(CHECK_ATTEMPTS):
            if driver.is_replication_ok(self.instance):
                if self.verify_heartbeat:
                    if driver.is_heartbeat_replication_ok(self.instance):
                        return
                else:
                    return

                driver.stop_slave(self.instance)
                sleep(1)
                driver.start_slave(self.instance)

            sleep(CHECK_SECONDS)

        raise EnvironmentError("Maximum number of attempts check replication")


class IsReplicationOkMigrate(IsReplicationOk):
    def do(self):
        self.verify_heartbeat = False
        return super(IsReplicationOkMigrate, self).do()


class IsReplicationOkRollback(IsReplicationOk):
    def do(self):
        pass

    def undo(self):
        return super(IsReplicationOkRollback, self).do()


'''
class ConfigureNodes(FoxHA):
    def __unicode__(self):
        return "Configuring FoxHA nodes..."

    @property
    def mode(self):
        if self.instance == self.infra.instances.first():
            return 'read_write'
        else:
            return 'read_only'

    @property
    def instance_dns(self):
        if self.instance.dns == self.instance.address:
            return self.instance.future_instance.dns
        return self.instance.dns

    def add_node(self, instance):
        self.provider.add_node(
            self.infra.name, self.instance_dns,
            instance.address, instance.port, self.mode, 'enabled'
        )

    def add_node2(self, name, instance, mode, status):
        self.provider.add_node(
            self.infra.name, name, instance.address,
            instance.port, mode, status
        )

    def delete_node(self, instance):
        self.provider.delete_node(self.infra.name, instance.address)



class AddTargetNodeDatabaseMigrate(ConfigureNodes):
    def __unicode__(self):
        return "Adding FoxHA node..."

    def do(self):
        self.add_node(self.instance.future_instance)

    def undo(self):
        self.delete_node(self.instance.future_instance)


class RemoveSourceNodeDatabaseMigrate(ConfigureNodes):

    def __unicode__(self):
        return "Removing FoxHA node..."

    def do(self):
        self.delete_node(self.instance)

    def undo(self):
        self.add_node(self.instance)
'''

class RecreateGroupDatabaseMigrate(FoxHA):

    def __unicode__(self):
        return "Reconfiguring FoxHA group..."

    @property
    def is_valid(self):
        return self.instance == self.infra.instances.first()

    def add_group(self, vip):
        self.provider.add_group(
            self.infra.name, self.infra.name, vip.vip_ip,
            self.mysql_fox_credentials.user,
            str(self.mysql_fox_credentials.password),
            self.mysql_replica_credentials.user,
            str(self.mysql_replica_credentials.password)
        )

    def delete_group(self):
        self.provider.delete_group(self.infra.name)

    def do(self):
        if not self.is_valid:
            return
        self.delete_group()
        self.add_group(self.future_vip)

    def undo(self):
        if not self.is_valid:
            return
        self.delete_group()
        self.add_group(self.vip)


class ConfigureNodes(FoxHA):
    def __unicode__(self):
        return "Configuring FoxHA nodes..."

    @property
    def mode(self):
        if self.instance == self.infra.instances.first():
            return 'read_write'
        else:
            return 'read_only'

    def add_node(self, instance, mode, status):
        self.provider.add_node(
            self.infra.name, instance.dns, instance.address,
            instance.port, mode, status
        )

    def delete_node(self, instance):
        self.provider.delete_node(self.infra.name, instance.address)


class MigrationAddNodeDestinyInstanceDisabled(ConfigureNodes):

    def do(self):
        self.add_node(self.instance.future_instance, 'read_only', 'disabled')

    def undo(self):
        self.delete_node(self.instance.future_instance)


class MigrationAddNodeSourceInstanceEnabledRollback(ConfigureNodes):

    def do(self):
        self.delete_node(self.instance.future_instance)
        self.delete_node(self.instance)

    def undo(self):
        self.add_node(self.instance, self.mode, 'enabled')
        self.add_node(self.instance.future_instance, 'read_only', 'disabled')


class MigrationAddNodeDestinyInstanceEnabled(ConfigureNodes):

    def do(self):
        self.add_node(self.instance.future_instance, self.mode, 'enabled')
        self.add_node(self.instance, 'read_only', 'disabled')
    def undo(self):
        self.delete_node(self.instance.future_instance)
        self.delete_node(self.instance)


class MigrationRemoveNodeSourceInstance(ConfigureNodes):

    def do(self):
        self.delete_node(self.instance)

    def undo(self):
        raise NotImplementedError
