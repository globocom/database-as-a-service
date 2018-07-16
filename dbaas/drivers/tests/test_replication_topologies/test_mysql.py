# -*- coding: utf-8 -*-
from drivers.replication_topologies.mysql import MySQLSingle
from drivers.replication_topologies.mysql import MySQLFoxHA
from drivers.tests.test_replication_topologies import AbstractReplicationTopologySettingsTestCase


class AbstractBaseMySQLTestCase(AbstractReplicationTopologySettingsTestCase):

    def _get_deploy_first_settings(self):
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

    def _get_deploy_last_settings(self):
        return (
            'workflow.steps.util.deploy.build_database.BuildDatabase',
            'workflow.steps.util.deploy.check_database_binds.CheckDatabaseBinds',
        )

    def _get_clone_settings(self):
        return self._get_deploy_first_settings() + self._get_deploy_last_settings() + (
            'workflow.steps.util.clone.clone_database.CloneDatabase',
        ) + self._get_monitoring_settings()

    def _get_resize_extra_steps(self):
        return (
            'workflow.steps.util.database.CheckIsUp',
            'workflow.steps.util.database.StartSlave',
            'workflow.steps.util.agents.Start',
            'workflow.steps.util.database.WaitForReplication',
        )

class TestMySQLSingle(AbstractBaseMySQLTestCase):

    def _get_replication_topology_driver(self):
        return MySQLSingle()

    def _get_deploy_settings(self):
        return [{
            'Creating virtual machine': (
                'workflow.steps.util.vm.CreateVirtualMachineNewInfra',
            )}, {
            'Creating dns': (
                'workflow.steps.util.dns.CreateDNS',
            )}, {
            'Creating disk': (
                'workflow.steps.util.disk.CreateExport',
            )}, {
            'Waiting VMs': (
                'workflow.steps.util.vm.WaitingBeReady',
                'workflow.steps.util.vm.UpdateOSDescription'
            )}, {
            'Configuring database': (
                'workflow.steps.util.infra.UpdateEndpoint',
                'workflow.steps.util.plan.InitializationForNewInfra',
                'workflow.steps.util.plan.ConfigureForNewInfra',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.database.StartMonit',
            )}, {
            'Check DNS': (
                'workflow.steps.util.dns.CheckIsReady',
            )}, {
            'Creating Database': (
                'workflow.steps.util.database.Create',
            )}, {
            'Creating monitoring and alarms': (
                'workflow.steps.util.zabbix.CreateAlarms',
                'workflow.steps.util.db_monitor.CreateInfraMonitoring',
            )
        }]

    def _get_restore_snapshot_settings(self):
        return [{
            'Disable monitoring': (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
            )}, {
            'Restoring': (
                'workflow.steps.util.disk.RestoreSnapshot',
            )}, {
            'Stopping datbase': (
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.CheckIsDown',
            )}, {
            'Configuring': (
                'workflow.steps.util.disk.AddDiskPermissionsRestoredDisk',
                'workflow.steps.util.disk.UnmountOldestExportRestore',
                'workflow.steps.util.disk.MountNewerExportRestore',
                'workflow.steps.util.disk.ConfigureFstabRestore',
                'workflow.steps.util.plan.ConfigureRestore',
            )}, {
            'Starting database': (
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
            )}, {
            'Old data': (
                'workflow.steps.util.disk.BackupRestore',
                'workflow.steps.util.disk.UpdateRestore',
            )}, {
            'Enabling monitoring': (
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
            )
        }]


class TestMySQLFoxHA(AbstractBaseMySQLTestCase):

    def _get_replication_topology_driver(self):
        return MySQLFoxHA()

    def _get_deploy_first_settings(self):
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
            'workflow.steps.mysql.deploy.check_replication.CheckReplicationFoxHA',
            'workflow.steps.util.deploy.config_backup_log.ConfigBackupLog',
            'workflow.steps.util.deploy.check_database_connection.CheckDatabaseConnection',
            'workflow.steps.util.deploy.check_dns.CheckDns',
            'workflow.steps.util.deploy.start_monit.StartMonit',
        )

    def _get_deploy_last_settings(self):
        return (
            'workflow.steps.util.deploy.build_database.BuildDatabase',
            'workflow.steps.util.deploy.check_database_binds.CheckDatabaseBinds',
        )

    def _get_deploy_settings(self):
        return [{
            'Creating virtual machine': (
                'workflow.steps.util.vm.CreateVirtualMachineNewInfra',
            )}, {
            'Creating VIP': (
                'workflow.steps.util.network.CreateVip',
                'workflow.steps.util.dns.RegisterDNSVip',
            )}, {
            'Creating dns': (
                'workflow.steps.util.dns.CreateDNS',
            )}, {
            'Creating disk': (
                'workflow.steps.util.disk.CreateExport',
            )}, {
            'Waiting VMs': (
                'workflow.steps.util.vm.WaitingBeReady',
                'workflow.steps.util.vm.UpdateOSDescription',
                'workflow.steps.util.vm.CheckHostNameAndReboot',
            )}, {
            'Check hostname': (
                'workflow.steps.util.vm.WaitingBeReady',
                'workflow.steps.util.vm.CheckHostName',
            )}, {
            'Check puppet': (
                'workflow.steps.util.puppet.ExecuteIfProblem',
                'workflow.steps.util.puppet.WaitingBeDone',
                'workflow.steps.util.puppet.CheckStatus',
            )}, {
            'Configure foreman': (
                'workflow.steps.util.foreman.SetupDSRC',
            )}, {
            'Running puppet': (
                'workflow.steps.util.puppet.Execute',
                'workflow.steps.util.puppet.CheckStatus',
            )}, {
            'Configuring database': (
                'workflow.steps.util.plan.InitializationForNewInfra',
                'workflow.steps.util.plan.ConfigureForNewInfra',
                'workflow.steps.util.database.Start',
            )}, {
            'Check database': (
                'workflow.steps.util.plan.StartReplicationNewInfra',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.database.StartMonit',
            )}, {
            'FoxHA configure': (
                'workflow.steps.util.fox.ConfigureGroup',
                'workflow.steps.util.fox.ConfigureNode',
            )}, {
            'FoxHA start': (
                'workflow.steps.util.fox.Start',
                'workflow.steps.util.fox.IsReplicationOk'
            )}, {
            'Check DNS': (
                'workflow.steps.util.dns.CheckIsReady',
            )}, {
            'Creating Database': (
                'workflow.steps.util.database.Create',
            )}, {
            'Creating monitoring and alarms': (
                'workflow.steps.util.mysql.CreateAlarmsVip',
                'workflow.steps.util.zabbix.CreateAlarms',
                'workflow.steps.util.db_monitor.CreateInfraMonitoring',
            )
        }]

    def _get_restore_snapshot_settings(self):
        return [{
            'Disable monitoring': (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
            )}, {
            'Restoring': (
                'workflow.steps.util.mysql.RestoreSnapshotMySQL',
            )}, {
            'Stopping datbase': (
                'workflow.steps.util.mysql.SaveMySQLBinlog',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.CheckIsDown',
            )}, {
            'Configuring': (
                'workflow.steps.util.mysql.AddDiskPermissionsRestoredDiskMySQL',
                'workflow.steps.util.mysql.UnmountOldestExportRestoreMySQL',
                'workflow.steps.util.mysql.MountNewerExportRestoreMySQL',
                'workflow.steps.util.mysql.ConfigureFstabRestoreMySQL',
                'workflow.steps.util.disk.RemoveDeprecatedFiles',
                'workflow.steps.util.plan.ConfigureRestore',
            )}, {
            'Starting database': (
                'workflow.steps.util.database.Start',
            )}, {
            'Configuring replication': (
                'workflow.steps.util.mysql.SetMasterRestore',
            )}, {
            'Start slave': (
                'workflow.steps.util.mysql.StartSlave',
            )}, {
            'Configure FoxHA': (
                'workflow.steps.util.mysql.ConfigureFoxHARestore',
            )}, {
            'Check database': (
                'workflow.steps.util.database.CheckIsUp',
            )}, {
            'Old data': (
                'workflow.steps.util.disk.BackupRestore',
                'workflow.steps.util.disk.UpdateRestore',
            )}, {
            'Enabling monitoring': (
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
            )
        }]

    def _get_upgrade_steps_extra(self):
        return super(TestMySQLFoxHA, self)._get_upgrade_steps_extra() + (
            'workflow.steps.util.vm.CheckHostName',
            'workflow.steps.util.puppet.ExecuteIfProblem',
            'workflow.steps.util.puppet.WaitingBeDone',
            'workflow.steps.util.puppet.CheckStatus',
            'workflow.steps.util.foreman.SetupDSRC',
            'workflow.steps.util.puppet.Execute',
            'workflow.steps.util.puppet.CheckStatus',
        )

    def _get_upgrade_settings(self):
        return [{
            self._get_upgrade_steps_initial_description(): (
                'workflow.steps.util.zabbix.DestroyAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
            ),
        }] + [{
            self._get_upgrade_steps_description(): (
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.CheckIsDown',
                'workflow.steps.util.foreman.DeleteHost',
                'workflow.steps.util.vm.Stop',
                'workflow.steps.util.vm.InstallNewTemplate',
                'workflow.steps.util.vm.Start',
                'workflow.steps.util.vm.WaitingBeReady',
                'workflow.steps.util.vm.UpdateOSDescription',
            ) + self._get_upgrade_steps_extra() + (
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
            ),
        }] + self._get_upgrade_steps_final()

    def _get_reinstallvm_steps(self):
        return [{
            'Disable monitoring and alarms': (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
            ),
        }] + [{
            'Reinstall VM': (
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.foreman.DeleteHost',
                'workflow.steps.util.vm.Stop',
                'workflow.steps.util.vm.ReinstallTemplate',
                'workflow.steps.util.vm.Start',
                'workflow.steps.util.vm.WaitingBeReady',
                'workflow.steps.util.vm.UpdateOSDescription',
            ),
        }] + [{
            'Configure Puppet': (
                'workflow.steps.util.vm.CheckHostName',
                'workflow.steps.util.puppet.ExecuteIfProblem',
                'workflow.steps.util.puppet.WaitingBeDone',
                'workflow.steps.util.puppet.CheckStatus',
                'workflow.steps.util.foreman.SetupDSRC',
                'workflow.steps.util.puppet.Execute',
                'workflow.steps.util.puppet.CheckStatus',
            ),
        }] + [{
            'Start Database': (
                'workflow.steps.util.plan.Initialization',
                'workflow.steps.util.plan.Configure',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
            ),
        }] + self._get_reinstallvm_steps_final()

    def _get_reinstall_vm_extra_steps(self):
        return [{
            'Configure Puppet': (
                'workflow.steps.util.vm.CheckHostName',
                'workflow.steps.util.puppet.ExecuteIfProblem',
                'workflow.steps.util.puppet.WaitingBeDone',
                'workflow.steps.util.puppet.CheckStatus',
                'workflow.steps.util.foreman.SetupDSRC',
                'workflow.steps.util.puppet.Execute',
                'workflow.steps.util.puppet.CheckStatus',
            ),
        }]