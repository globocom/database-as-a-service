from time import sleep
from dbaas_foxha.dbaas_api import DatabaseAsAServiceApi
from dbaas_foxha.provider import FoxHAProvider
from dbaas_credentials.models import CredentialType
from util import get_credentials_for
from base import BaseInstanceStep
from physical.models import Vip
from drivers.errors import ReplicationNotRunningError


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
        return "Checking replication status..."

    def do(self):
        if self.host_migrate and self.instance.hostname.future_host:
            self.instance.address = self.instance.hostname.future_host.address

        for _ in range(CHECK_ATTEMPTS):

            try:
                repl_ok = self.driver.is_replication_ok(self.instance)
            except ReplicationNotRunningError:
                repl_ok = False
                self.driver.stop_slave(self.instance)
                sleep(1)
                self.driver.start_slave(self.instance)

            if not repl_ok:
                sleep(CHECK_SECONDS)
                continue

            repl_ht_ok = True
            if self.verify_heartbeat:
                repl_ht_ok = self.driver.is_heartbeat_replication_ok(
                    self.instance)
                if not repl_ht_ok:
                    sleep(CHECK_SECONDS)
                    master_instance = self.driver.get_master_instance()
                    host = master_instance.hostname
                    self.driver.stop_agents(host)
                    sleep(1)
                    self.driver.start_agents(host)

            if repl_ok and repl_ht_ok:
                return

        raise EnvironmentError("Maximum number of attempts check replication")

class IsReplicationOkRollback(IsReplicationOk):
    def __unicode__(self):
        return "Checking replication status if rollback..."

    def do(self):
        pass

    def undo(self):
        return super(IsReplicationOkRollback, self).do()


class IsReplicationOkMigrate(IsReplicationOk):
    def do(self):
        self.verify_heartbeat = False
        return super(IsReplicationOkMigrate, self).do()


class checkDatabaseAndFoxHAMaster(FoxHA):

    def __unicode__(self):
        return "Checking database and FoxHA Master..."

    def do(self):
        master_instance = self.driver.get_master_instance()
        if not master_instance:
            raise EnvironmentError(
                "There is no master instance. Check FoxHA and database" \
                " read-write instances."
            )


class checkDatabaseAndFoxHAMasterRollback(checkDatabaseAndFoxHAMaster):
    def __unicode__(self):
        return "Checking database and FoxHA Master if rollback..."

    def do(self):
        pass

    def undo(self):
        return super(checkDatabaseAndFoxHAMasterRollback, self).do()


class checkReplicationStatus(FoxHA):
    def __unicode__(self):
        return "Checking replication status..."

    def __init__(self, instance):
        super(FoxHA, self).__init__(instance)
        self.instances = self.infra.instances.all()

    def get_master_instance(self):
        master_instance = self.driver.get_master_instance()
        if not master_instance:
            sleep(CHECK_SECONDS)
        master_instance = self.driver.get_master_instance()
        if not master_instance:
            raise EnvironmentError(
                "There is no master instance. Check FoxHA and database" \
                " read-write instances."
            )
        return master_instance

    def check_replication_is_running(self, instance):
        try:
            self.driver.get_replication_info(instance)
        except ReplicationNotRunningError:
            self.driver.stop_slave(instance)
            sleep(1)
            self.driver.start_slave(instance)
            sleep(1)
            self.driver.get_replication_info(instance)

    def check_replication_delay(self, instance):
        for _ in range(CHECK_ATTEMPTS):
            if self.driver.is_replication_ok(instance):
                return
            sleep(CHECK_SECONDS)
        raise EnvironmentError("Maximum number of attempts check replication")

    def check_heartbeat(self):
        master_instance = self.get_master_instance()
        hb_ok = self.driver.is_heartbeat_replication_ok(master_instance)
        if not hb_ok:
            host = master_instance.hostname
            self.driver.stop_agents(host)
            sleep(1)
            self.driver.start_agents(host)
            sleep(1)
            hb_ok = self.driver.is_heartbeat_replication_ok(master_instance)
            if not hb_ok:
                raise EnvironmentError("Check heartbeat delay.")

    def do(self):
        for instance in self.instances:
            self.check_replication_is_running(instance)
        for instance in self.instances:
            self.check_replication_delay(instance)
        self.check_heartbeat()


class checkReplicationStatusRollback(checkReplicationStatus):
    def __unicode__(self):
        return "Checking replication status if rollback..."

    def do(self):
        pass

    def undo(self):
        return super(checkReplicationStatusRollback, self).do()