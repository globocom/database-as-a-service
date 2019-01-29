from backup.tasks import mysql_binlog_save
from workflow.steps.mysql.util import get_replication_information_from_file, \
    change_master_to, start_slave
from volume_provider import AddAccessRestoredVolume, MountDataVolumeRestored, \
    RestoreSnapshot, UnmountActiveVolume
from zabbix import ZabbixStep
from base import BaseInstanceStep
from workflow.steps.util import test_bash_script_error
from util import exec_remote_command_host


class MySQLStep(BaseInstanceStep):

    def __init__(self, instance):
        super(MySQLStep, self).__init__(instance)
        self.driver = self.infra.get_driver()

    def undo(self):
        pass

    def run_script(self, script):
        output = {}
        return_code = exec_remote_command_host(
            self.host, script, output
        )
        if return_code != 0:
            raise EnvironmentError(
                'Could not execute script {}: {}'.format(
                    return_code, output
                )
            )

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
    DiskRestoreMySQL, UnmountActiveVolume
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


class SetFilePermission(MySQLStep):
    def __unicode__(self):
        return "Setting file permition..."

    @property
    def script(self):
        return test_bash_script_error() + """
            chown mysql:mysql /data
            die_if_error "Error executing chown mysql:mysql /data"
            chown -R mysql:mysql /data/*
            die_if_error "Error executing chown -R mysql:mysql /data/*"
            """

    def do(self):

        self.run_script(self.script)


class RunMySQLUpgrade(MySQLStep):
    def __unicode__(self):
        return "Executing mysql_upgrade..."

    @property
    def script(self):
        return "mysql_upgrade -u{} -p{}".format(
            self.infra.user, self.infra.password)

    def do(self):
        self.run_script(self.script)


class AuditPlugin(MySQLStep):
    @property
    def audit_plugin_status(self):
        query = """SELECT plugin_name, plugin_status
        FROM INFORMATION_SCHEMA.PLUGINS
        WHERE plugin_name = 'audit_log';"""

        ret_query = self.driver.query(
            query_string=query, instance=self.instance)
        if len(ret_query) == 0:
            return False
        if ret_query[0]['plugin_status'] != 'ACTIVE':
            return False
        return True

class InstallAuditPlugin(AuditPlugin):
    def __unicode__(self):
        return "Installing audit plugin..."

    @property
    def query(self):
        return "INSTALL PLUGIN audit_log SONAME 'audit_log.so';"

    def do(self):
        if not self.audit_plugin_status:
            self.driver.query(query_string=self.query, instance=self.instance)

class CheckIfAuditPluginIsInstalled(AuditPlugin):
    def __unicode__(self):
        return "Checking if audit plugin is installed..."

    def do(self):
        if not self.audit_plugin_status:
            raise EnvironmentError('The audit plugin is not installed.')

class SkipSlaveStart(MySQLStep):
    def __unicode__(self):
        return "Skipping slave start parameter..."

    @property
    def script(self):
        return "echo 'skip_slave_start = 1' >> /etc/my.cnf"

    def do(self):
        self.run_script(self.script)


class DisableLogBin(MySQLStep):
    def __unicode__(self):
        return "Disable binary loggin..."

    @property
    def script(self):
        return "sed -e 's/^log_bin/#log_bin/' -i /etc/my.cnf"

    def do(self):
        self.run_script(self.script)