# -*- coding: utf-8 -*-
import logging
from util import get_credentials_for
from dbaas_credentials.models import CredentialType
from dbaas_foxha.provider import FoxHAProvider
from dbaas_foxha.dbaas_api import DatabaseAsAServiceApi
from base import BaseTopology

LOG = logging.getLogger(__name__)


class BaseMysql(BaseTopology):
    def deploy_first_steps(self):
        return (
            'workflow.steps.util.deploy.build_databaseinfra.BuildDatabaseInfra',
            'workflow.steps.mysql.deploy.create_virtualmachines.CreateVirtualMachine',
            'workflow.steps.mysql.deploy.create_secondary_ip.CreateSecondaryIp',
            'workflow.steps.mysql.deploy.create_dns.CreateDns',
            'workflow.steps.util.deploy.create_nfs.CreateNfs',
            'workflow.steps.mysql.deploy.init_database.InitDatabase',
            'workflow.steps.util.deploy.config_backup_log.ConfigBackupLog',
            'workflow.steps.util.deploy.check_database_connection.CheckDatabaseConnection',
            'workflow.steps.util.deploy.check_dns.CheckDns',
            'workflow.steps.util.deploy.start_monit.StartMonit',
        )

    def deploy_last_steps(self):
        return (
            'workflow.steps.util.deploy.build_database.BuildDatabase',
            'workflow.steps.util.deploy.check_database_binds.CheckDatabaseBinds',
        )

    def get_clone_steps(self):
        return self.deploy_first_steps() + self.deploy_last_steps() + (
            'workflow.steps.util.clone.clone_database.CloneDatabase',
        ) + self.monitoring_steps()

    def switch_master(self, driver):
        raise NotImplementedError()

    def check_instance_is_master(self, driver, instance):
        raise NotImplementedError

    def set_master(self, driver, instance):
        raise NotImplementedError

    def set_read_ip(self, driver, instance):
        raise NotImplementedError

    def get_database_agents(self):
        return ['monit']


class MySQLSingle(BaseMysql):

    def switch_master(self, driver):
        return True

    def check_instance_is_master(self, driver, instance):
        return True

    def set_master(self, driver, instance):
        raise True

    def set_read_ip(self, driver, instance):
        raise True

    @property
    def driver_name(self):
        return 'mysql_single'


class MySQLFoxHA(MySQLSingle):

    def get_restore_snapshot_steps(self):
        return (
            'workflow.steps.mysql.restore_snapshot.restore_snapshot.RestoreSnapshot',
            'workflow.steps.util.restore_snapshot.grant_nfs_access.GrantNFSAccess',
            'workflow.steps.util.restore_snapshot.make_export_snapshot.MySQLSaveBinlogPosition',
            'workflow.steps.mysql.restore_snapshot.stop_database.StopDatabase',
            'workflow.steps.mysql.restore_snapshot.umount_data_volume.UmountDataVolume',
            'workflow.steps.util.restore_snapshot.update_fstab.UpdateFstab',
            'workflow.steps.util.restore_snapshot.mount_data_volume.MountDataVolume',
            'workflow.steps.mysql.restore_snapshot.start_database_and_replication.StartDatabaseAndReplication',
            'workflow.steps.util.restore_snapshot.make_export_snapshot.MakeExportSnapshot',
            'workflow.steps.util.restore_snapshot.update_dbaas_metadata.UpdateDbaaSMetadata',
            'workflow.steps.util.restore_snapshot.clean_old_volumes.CleanOldVolumes',
        )

    def deploy_first_steps(self):
        return (
            'workflow.steps.util.deploy.build_databaseinfra.BuildDatabaseInfra',
            'workflow.steps.mysql.deploy.create_virtualmachines_fox.CreateVirtualMachine',
            'workflow.steps.mysql.deploy.create_vip.CreateVip',
            'workflow.steps.mysql.deploy.create_dns_foxha.CreateDnsFoxHA',
            'workflow.steps.util.deploy.create_nfs.CreateNfs',
            'workflow.steps.mysql.deploy.init_database_foxha.InitDatabaseFoxHA',
            'workflow.steps.mysql.deploy.check_pupet.CheckVMName',
            'workflow.steps.mysql.deploy.check_pupet.CheckPuppetIsRunning',
            'workflow.steps.mysql.deploy.config_vms_foreman.ConfigVMsForeman',
            'workflow.steps.mysql.deploy.run_pupet_setup.RunPuppetSetup',
            'workflow.steps.mysql.deploy.config_fox.ConfigFox',
            'workflow.steps.util.deploy.config_backup_log.ConfigBackupLog',
            'workflow.steps.util.deploy.check_database_connection.CheckDatabaseConnection',
            'workflow.steps.util.deploy.check_dns.CheckDns',
            'workflow.steps.util.deploy.start_monit.StartMonit',
        )

    def deploy_last_steps(self):
        return (
            'workflow.steps.util.deploy.build_database.BuildDatabase',
            'workflow.steps.util.deploy.check_database_binds.CheckDatabaseBinds',
        )

    def _get_fox_provider(self, driver):
        databaseinfra = driver.databaseinfra

        foxha_credentials = get_credentials_for(
            environment=databaseinfra.environment,
            credential_type=CredentialType.FOXHA
        )
        dbaas_api = DatabaseAsAServiceApi(databaseinfra, foxha_credentials)
        return FoxHAProvider(dbaas_api)

    def switch_master(self, driver):
        self._get_fox_provider(driver).switchover(
            group_name=driver.databaseinfra.name
        )

    def check_instance_is_master(self, driver, instance):
        return self._get_fox_provider(driver).node_is_master(
            group_name=driver.databaseinfra.name,
            node_ip=instance.address
        )

    def set_master(self, driver, instance):
        self._get_fox_provider(driver).set_master(
            group_name=driver.databaseinfra.name,
            node_ip=instance.address
        )

    def set_read_ip(self, driver, instance):
        self._get_fox_provider(driver).set_read_only(
            group_name=driver.databaseinfra.name,
            node_ip=instance.address
        )

    def get_database_agents(self):
        agents = ['httpd', '/etc/init.d/pt-heartbeat']
        return super(MySQLFoxHA, self).get_database_agents() + agents

    def add_database_instances_first_steps(self):
        return ()

    def add_database_instances_last_steps(self):
        return ()

    @property
    def driver_name(self):
        return 'mysql_foxha'
