from backup.tasks import mysql_binlog_save
from workflow.steps.mysql.util import get_replication_information_from_file, \
    change_master_to, start_slave
from disk import RestoreSnapshot, UnmountOldestExportRestore
from volume_provider import AddAccessRestoredVolume, MountDataVolumeRestored
from zabbix import ZabbixStep
from base import BaseInstanceStep


class MySQLStep(BaseInstanceStep):

    def undo(self):
        pass


class SetMasterRestore(MySQLStep):

    def __unicode__(self):
        return "Set master position..."

    def do(self):
        pair = self.restore.instances_pairs()[0]
        log_file, log_pos = get_replication_information_from_file(
            pair.master.hostname
        )

        secondary = pair.master
        if self.instance == secondary:
            secondary = pair.slave

        change_master_to(
            self.instance, secondary.hostname.address, log_file, log_pos
        )


class StartSlave(MySQLStep):

    def __unicode__(self):
        return "Start slave..."

    def do(self):
        start_slave(self.instance)


class ConfigureFoxHARestore(MySQLStep):

    def __unicode__(self):
        return "Configuring FoxHA..."

    def do(self):
        driver = self.infra.get_driver()
        if self.restore.is_master(self.instance):
            driver.set_master(self.instance)
        else:
            driver.set_read_ip(self.instance)


class SaveMySQLBinlog(MySQLStep):

    def __unicode__(self):
        return "Saving binlog position..."

    @property
    def is_valid(self):
        return self.restore.is_master(self.instance)

    def do(self):
        if not self.is_valid:
            return

        driver = self.infra.get_driver()
        client = driver.get_client(self.instance)
        mysql_binlog_save(client, self.instance)


class RestoreSnapshotMySQL(RestoreSnapshot):

    @property
    def snapshot(self):
        return self.restore.group.backups.first()

    @property
    def disk_host(self):
        return self.host


class DiskRestoreMySQL(MySQLStep):

    @property
    def is_valid(self):
        return True


class AddDiskPermissionsRestoredDiskMySQL(
    DiskRestoreMySQL, AddAccessRestoredVolume
):
    pass


class UnmountOldestExportRestoreMySQL(
    DiskRestoreMySQL, UnmountOldestExportRestore
):
    pass


class MountNewerExportRestoreMySQL(DiskRestoreMySQL, MountDataVolumeRestored):
    pass


class ZabbixVip(ZabbixStep):

    @property
    def is_valid(self):
        return self.instance == self.infra.instances.first()

    @property
    def vip_instance_dns(self):
        return self.zabbix_provider.mysql_infra_dns_from_endpoint_dns


class CreateAlarmsVip(ZabbixVip):

    def __unicode__(self):
        return "Creating monitoring to FoxHA Vip..."

    @property
    def is_valid(self):
        return self.instance == self.infra.instances.first()

    def do(self):
        if not self.is_valid:
            return

        extra = self.zabbix_provider.get_database_monitors_extra_parameters()
        self.zabbix_provider._create_database_monitors(
            host=self.vip_instance_dns, dbtype='mysql', alarm='yes', **extra
        )

    def undo(self):
        DestroyAlarmsVip(self.instance).do()


class DestroyAlarmsVip(ZabbixVip):

    def __unicode__(self):
        return "Destroying monitoring to FoxHA Vip..."

    def do(self):
        if not self.is_valid:
            return

        self.zabbix_provider.delete_instance_monitors(self.vip_instance_dns)

    def undo(self):
        CreateAlarmsVip(self.instance).do()
