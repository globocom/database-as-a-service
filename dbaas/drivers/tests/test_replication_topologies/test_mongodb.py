# -*- coding: utf-8 -*-
from drivers.replication_topologies.mongodb import MongoDBReplicaset
from drivers.replication_topologies.mongodb import MongoDBSingle
from drivers.tests.test_replication_topologies import AbstractReplicationTopologySettingsTestCase


class AbstractBaseMondodbTestCase(AbstractReplicationTopologySettingsTestCase):

    def _get_deploy_first_settings(self):
        return (
            'workflow.steps.util.deploy.build_databaseinfra.BuildDatabaseInfra',
            'workflow.steps.mongodb.deploy.create_virtualmachines.CreateVirtualMachine',
            'workflow.steps.util.deploy.create_dns.CreateDns',
            'workflow.steps.util.deploy.create_nfs.CreateNfs',
            'workflow.steps.mongodb.deploy.init_database.InitDatabaseMongoDB',
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


class TestMongoDBSingle(AbstractBaseMondodbTestCase):

    def _get_replication_topology_driver(self):
        return MongoDBSingle()

    def _get_upgrade_steps_extra(self):
        return \
            ('workflow.steps.mongodb.upgrade.vm.ChangeBinaryTo32',) + \
            super(TestMongoDBSingle, self)._get_upgrade_steps_extra() + (
                'workflow.steps.util.plan.ConfigureOnlyDBConfigFile',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.CheckIsDown',
                'workflow.steps.mongodb.upgrade.vm.ChangeBinaryTo34',
                'workflow.steps.util.plan.ConfigureForUpgradeOnlyDBConfigFile',
            )

    def _get_upgrade_steps_final(self):
        return [{
            'Setting feature compatibility version 3.4': (
                'workflow.steps.mongodb.upgrade.database.SetFeatureCompatibilityVersion34',
            ),
        }] + super(TestMongoDBSingle, self)._get_upgrade_steps_final()

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
                'workflow.steps.util.plan.InitializationForNewInfra',
                'workflow.steps.util.plan.ConfigureForNewInfra',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.infra.UpdateEndpoint',
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


class TestMongoDBReplicaset(AbstractBaseMondodbTestCase):

    def _get_replication_topology_driver(self):
        return MongoDBReplicaset()

    def _get_upgrade_steps_description(self):
        return 'Upgrading to MongoDB 3.2'

    def _get_upgrade_steps_extra(self):
        return (
            'workflow.steps.mongodb.upgrade.vm.ChangeBinaryTo32',
            'workflow.steps.util.plan.InitializationForUpgrade',
            'workflow.steps.util.plan.Configure',
        )

    def _get_upgrade_steps_final(self):
        return [{
            'Upgrading to MongoDB 3.4': (
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.CheckIsDown',
                'workflow.steps.mongodb.upgrade.vm.ChangeBinaryTo34',
                'workflow.steps.util.plan.ConfigureForUpgradeOnlyDBConfigFile',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
            ),
        }] + [{
            'Setting feature compatibility version 3.4': (
                'workflow.steps.mongodb.upgrade.database.SetFeatureCompatibilityVersion34',
            ),
        }] + super(TestMongoDBReplicaset, self)._get_upgrade_steps_final()

    def _get_add_database_instances_middle_settings(self):
        return (
            'workflow.steps.util.plan.Initialization',
            'workflow.steps.util.plan.Configure',
            'workflow.steps.util.database.Start',
            'workflow.steps.mongodb.horizontal_elasticity.database.AddInstanceToReplicaSet',
        )

    def _get_resize_oplog_steps(self):
        return [{
            'Resize oplog': (
                'workflow.steps.util.database.ValidateOplogSizeValue',
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.CheckIfSwitchMaster',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.CheckIsDown',
                'workflow.steps.util.plan.ConfigureForResizeLog',
                'workflow.steps.util.database.StartForResizeLog',
                'workflow.steps.util.database.CheckIsUpForResizeLog',
                'workflow.steps.util.database.ResizeOpLogSize',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.CheckIsDown',
                'workflow.steps.util.plan.ConfigureOnlyDBConfigFile',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',

            )
        }] + self._get_change_parameter_steps_final()

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
                'workflow.steps.util.plan.InitializationForNewInfra',
                'workflow.steps.util.plan.ConfigureForNewInfra',
                'workflow.steps.util.database.Start',
            )}, {
            'Check Database': (
                'workflow.steps.util.plan.StartReplicationFirstNodeNewInfra',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.infra.UpdateEndpoint',
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
                'workflow.steps.util.disk.CleanDataMongoDB',
                'workflow.steps.util.plan.ConfigureRestore',
            )}, {
            'Starting database': (
                'workflow.steps.util.database.Start',
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
