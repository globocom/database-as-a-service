# -*- coding: utf-8 -*-
from base import BaseTopology


class BaseRedis(BaseTopology):
    def deploy_first_steps(self):
        return (
            'workflow.steps.redis.deploy.build_databaseinfra.BuildDatabaseInfra',
            'workflow.steps.redis.deploy.create_virtualmachines.CreateVirtualMachine',
            'workflow.steps.redis.deploy.create_dns.CreateDns',
            'workflow.steps.util.deploy.create_nfs.CreateNfs',
            'workflow.steps.redis.deploy.init_database.InitDatabaseRedis',
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
            'workflow.steps.redis.clone.clone_database.CloneDatabase',
        ) + self.monitoring_steps()

    def get_upgrade_steps_extra(self):
        return (
            'workflow.steps.util.plan.InitializationForUpgrade',
            'workflow.steps.util.plan.ConfigureForUpgrade',
            'workflow.steps.util.pack.Configure',
        )

    def get_resize_extra_steps(self):
        return super(BaseRedis, self).get_resize_extra_steps() + (
            'workflow.steps.util.infra.Memory',
        )

    def add_database_instances_first_steps(self):
        return ()

    def add_database_instances_last_steps(self):
        return ()


class RedisSingle(BaseRedis):

    @property
    def driver_name(self):
        return 'redis_single'

    def deploy_quantity_of_instances(self):
        return 1

    def get_deploy_steps(self):
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
                # new step: update endpoint and dnsendpoint
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



class RedisSentinel(BaseRedis):

    def get_upgrade_steps_final(self):
        return [{
            'Resetting Sentinel': (
                'workflow.steps.redis.upgrade.sentinel.Reset',
                'workflow.steps.util.database.SetSlave',
            ),
        }] + super(RedisSentinel, self).get_upgrade_steps_final()

    def get_reinstallvm_steps_final(self):
        return [{
            'Resetting Sentinel': (
                'workflow.steps.redis.upgrade.sentinel.ResetAllSentinel',
                'workflow.steps.util.database.SetSlave',
            ),
        }] + super(RedisSentinel, self).get_reinstallvm_steps_final()


    def get_add_database_instances_middle_steps(self):
        return (
            'workflow.steps.util.plan.Initialization',
            'workflow.steps.util.plan.Configure',
            'workflow.steps.util.pack.Configure',
            'workflow.steps.util.database.Start',
            'workflow.steps.redis.horizontal_elasticity.database.AddInstanceToRedisCluster',
        )

    @property
    def driver_name(self):
        return 'redis_sentinel'

    def get_restore_snapshot_steps(self):
        return (
            'workflow.steps.util.restore_snapshot.restore_snapshot.RestoreSnapshot',
            'workflow.steps.util.restore_snapshot.grant_nfs_access.GrantNFSAccess',
            'workflow.steps.util.restore_snapshot.stop_database.StopDatabase',
            'workflow.steps.util.restore_snapshot.umount_data_volume.UmountDataVolume',
            'workflow.steps.util.restore_snapshot.update_fstab.UpdateFstab',
            'workflow.steps.util.restore_snapshot.mount_data_volume.MountDataVolume',
            'workflow.steps.redis.restore_snapshot.start_database.StartDatabase',
            'workflow.steps.util.restore_snapshot.make_export_snapshot.MakeExportSnapshot',
            'workflow.steps.util.restore_snapshot.update_dbaas_metadata.UpdateDbaaSMetadata',
            'workflow.steps.util.restore_snapshot.clean_old_volumes.CleanOldVolumes',
        )


class RedisNoPersistence(RedisSingle):
    pass


class RedisSentinelNoPersistence(RedisSentinel):
    pass


class RedisCluster(BaseRedis):

    def deploy_quantity_of_instances(self):
        return 6

    def get_deploy_steps(self):
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
            )}, {
            'Configuring Cluster': (
                'workflow.steps.redis.cluster.CreateCluster',
                'workflow.steps.redis.cluster.CheckClusterStatus',
                'workflow.steps.redis.cluster.SetInstanceShardTag',
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

    def get_destroy_steps(self):
        return super(RedisCluster, self).get_destroy_steps()

    def get_restore_snapshot_steps(self):
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
                'workflow.steps.redis.cluster.SaveNodeConfig'
            )}, {
            'Configuring': (
                'workflow.steps.util.disk.AddDiskPermissionsRestoredDisk',
                'workflow.steps.util.disk.UnmountOldestExportRestore',
                'workflow.steps.util.disk.MountNewerExportRestore',
                'workflow.steps.util.disk.ConfigureFstabRestore',
                'workflow.steps.util.disk.CleanData',
                'workflow.steps.util.plan.InitializationRestore',
                'workflow.steps.util.plan.ConfigureRestore',
                'workflow.steps.redis.cluster.RestoreNodeConfig'
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

    @property
    def driver_name(self):
        return 'redis_cluster'
