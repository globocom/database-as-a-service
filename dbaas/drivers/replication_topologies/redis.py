# -*- coding: utf-8 -*-
from base import BaseTopology, InstanceDeploy
from physical.models import Instance


class BaseRedis(BaseTopology):
    def deploy_first_steps(self):
        return (
            'workflow.steps.redis.deploy.build_databaseinfra.BuildDatabaseInfra',
            'workflow.steps.redis.deploy.create_virtualmachines.CreateVirtualMachine',
            'workflow.steps.redis.deploy.create_dns.CreateDns',
            'workflow.steps.util.deploy.create_nfs.CreateNfs',
            'workflow.steps.redis.deploy.init_database.InitDatabaseRedis',
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
            'workflow.steps.util.volume_provider.MountDataVolume',
            'workflow.steps.util.plan.InitializationForUpgrade',
            'workflow.steps.util.plan.ConfigureForUpgrade',
            'workflow.steps.util.metric_collector.ConfigureTelegraf',
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

    def deploy_instances(self):
        return [[InstanceDeploy(Instance.REDIS, 6379)]]

    def get_deploy_steps(self):
        return [{
            'Creating virtual machine': (
                'workflow.steps.util.host_provider.CreateVirtualMachine',
            )}, {
            'Creating dns': (
                'workflow.steps.util.dns.CreateDNS',
            )}, {
            'Creating disk': (
                'workflow.steps.util.volume_provider.NewVolume',
            )}, {
            'Waiting VMs': (
                'workflow.steps.util.vm.WaitingBeReady',
                'workflow.steps.util.vm.UpdateOSDescription'
            )}, {
            'Configuring database': (
                'workflow.steps.util.volume_provider.MountDataVolume',
                'workflow.steps.util.plan.InitializationForNewInfra',
                'workflow.steps.util.plan.ConfigureForNewInfra',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.metric_collector.RestartTelegraf',
                'workflow.steps.util.infra.UpdateEndpoint',
            )}, {
            'Check DNS': (
                'workflow.steps.util.dns.CheckIsReady',
            )}, {
            'Creating Database': (
                'workflow.steps.util.database.Create',
            )}, {
            'Check ACL': (
                'workflow.steps.util.acl.BindNewInstance',
            )}, {
            'Creating monitoring and alarms': (
                'workflow.steps.util.zabbix.CreateAlarms',
                'workflow.steps.util.db_monitor.CreateInfraMonitoring',
            )
        }]

    def get_restore_snapshot_steps(self):
        return [{
            'Disable monitoring': (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
            )}, {
            'Restoring': (
                'workflow.steps.util.volume_provider.RestoreSnapshot',
            )}, {
            'Stopping datbase': (
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.CheckIsDown',
            )}, {
            'Configuring': (
                'workflow.steps.util.volume_provider.AddAccessRestoredVolume',
                'workflow.steps.util.volume_provider.UnmountActiveVolume',
                'workflow.steps.util.volume_provider.MountDataVolumeRestored',
                'workflow.steps.util.plan.ConfigureRestore',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
            )}, {
            'Starting database': (
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.metric_collector.RestartTelegraf',
            )}, {
            'Old data': (
                'workflow.steps.util.volume_provider.TakeSnapshot',
                'workflow.steps.util.volume_provider.UpdateActiveDisk',
            )}, {
            'Enabling monitoring': (
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
            )
        }]


class RedisSentinel(BaseRedis):

    def get_upgrade_steps_final(self):
        return [{
            'Resetting Sentinel': (
                'workflow.steps.redis.upgrade.sentinel.ResetAllSentinel',
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
            'workflow.steps.util.volume_provider.MountDataVolume',
            'workflow.steps.util.plan.Initialization',
            'workflow.steps.util.plan.Configure',
            'workflow.steps.util.metric_collector.ConfigureTelegraf',
            'workflow.steps.util.database.Start',
            'workflow.steps.util.metric_collector.RestartTelegraf',
            'workflow.steps.redis.horizontal_elasticity.database.AddInstanceToRedisCluster',
        )

    @property
    def driver_name(self):
        return 'redis_sentinel'

    def get_restore_snapshot_steps(self):
        return [{
            'Disable monitoring': (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
            )}, {
            'Restoring': (
                'workflow.steps.util.volume_provider.RestoreSnapshot',
            )}, {
            'Stopping datbase': (
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.CheckIsDown',
            )}, {
            'Configuring': (
                'workflow.steps.util.volume_provider.AddAccessRestoredVolume',
                'workflow.steps.util.volume_provider.UnmountActiveVolume',
                'workflow.steps.util.volume_provider.MountDataVolumeRestored',
                'workflow.steps.util.disk.CleanData',
                'workflow.steps.util.disk.RemoveDeprecatedFiles',
                'workflow.steps.util.plan.ConfigureRestore',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
            )}, {
            'Starting database': (
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.metric_collector.RestartTelegraf',
            )}, {
            'Configuring sentinel': (
                'workflow.steps.redis.upgrade.sentinel.ResetAllSentinel',
                'workflow.steps.util.database.SetSlaveRestore',
            )}, {
            'Old data': (
                'workflow.steps.util.volume_provider.TakeSnapshot',
                'workflow.steps.util.volume_provider.UpdateActiveDisk',
            )}, {
            'Check ACL': (
                'workflow.steps.util.acl.BindNewInstance',
            )}, {
            'Enabling monitoring': (
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
            )
        }]

    def deploy_instances(self):
        return [[
            InstanceDeploy(Instance.REDIS, 6379),
            InstanceDeploy(Instance.REDIS_SENTINEL, 26379)
        ], [
            InstanceDeploy(Instance.REDIS, 6379),
            InstanceDeploy(Instance.REDIS_SENTINEL, 26379)
        ], [
            InstanceDeploy(Instance.REDIS_SENTINEL, 26379),
        ]]

    def get_deploy_steps(self):
        return [{
            'Creating virtual machine': (
                'workflow.steps.util.host_provider.CreateVirtualMachine',
            )}, {
            'Creating dns': (
                'workflow.steps.util.dns.CreateDNS',
            )}, {
            'Creating disk': (
                'workflow.steps.util.volume_provider.NewVolume',
            )}, {
            'Waiting VMs': (
                'workflow.steps.util.vm.WaitingBeReady',
                'workflow.steps.util.vm.UpdateOSDescription'
            )}, {
            'Configuring database': (
                'workflow.steps.util.volume_provider.MountDataVolume',
                'workflow.steps.util.plan.InitializationForNewInfraSentinel',
                'workflow.steps.util.plan.ConfigureForNewInfraSentinel',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
            )}, {
            'Starting database': (
                'workflow.steps.util.database.StartSentinel',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.metric_collector.RestartTelegraf',
            )}, {
            'Configuring sentinel': (
                'workflow.steps.redis.upgrade.sentinel.Reset',
                'workflow.steps.util.database.SetSlave'
            )}, {
            'Check DNS': (
                'workflow.steps.util.dns.CheckIsReady',
            )}, {
            'Creating Database': (
                'workflow.steps.util.database.Create',
            )}, {
            'Check ACL': (
                'workflow.steps.util.acl.BindNewInstance',
            )}, {
            'Creating monitoring and alarms': (
                'workflow.steps.util.sentinel.CreateAlarmsNewInfra',
                'workflow.steps.util.db_monitor.CreateInfraMonitoring',
            )
        }]

    def get_host_migrate_steps_cleaning_up(self):
        return (
            'workflow.steps.util.volume_provider.DestroyOldEnvironment',
            'workflow.steps.util.host_provider.DestroyVirtualMachineMigrate',
            'workflow.steps.redis.upgrade.sentinel.ResetAllSentinel',
        )

    def get_base_host_migrate_steps(self):
        return (
            'workflow.steps.util.vm.ChangeMaster',
            'workflow.steps.util.database.CheckIfSwitchMaster',
            'workflow.steps.util.host_provider.CreateVirtualMachineMigrate',
            'workflow.steps.util.volume_provider.NewVolume',
            'workflow.steps.util.vm.WaitingBeReady',
            'workflow.steps.util.vm.UpdateOSDescription',
            'workflow.steps.util.volume_provider.MountDataVolume',
            'workflow.steps.util.plan.Initialization',
            'workflow.steps.util.plan.Configure',
            'workflow.steps.util.database.Start',
            'workflow.steps.util.database.CheckIsUp',
            'workflow.steps.util.vm.CheckAccessToMaster',
            'workflow.steps.util.vm.CheckAccessFromMaster',
            'workflow.steps.util.acl.ReplicateAclsMigrate',
            'workflow.steps.redis.upgrade.sentinel.ResetAllSentinel',
            'workflow.steps.util.database.SetSlave',
            'workflow.steps.util.database.WaitForReplication',
            'workflow.steps.redis.horizontal_elasticity.database.SetNotEligible',
            'workflow.steps.util.metric_collector.ConfigureTelegraf',
            'workflow.steps.util.metric_collector.RestartTelegraf',
            'workflow.steps.util.zabbix.DestroyAlarms',
            'workflow.steps.util.dns.ChangeEndpoint',
            'workflow.steps.util.dns.CheckIsReady',
            'workflow.steps.util.zabbix.CreateAlarms',
            'workflow.steps.util.disk.ChangeSnapshotOwner',
        )

    def get_host_migrate_steps(self):
        return [{
            'Migrating':
                self.get_base_host_migrate_steps() +
                self.get_host_migrate_steps_cleaning_up()
        }]

    def get_database_migrate_steps(self):
        return [{
            'Migrating': self.get_base_host_migrate_steps()
        }, {
            'Cleaning up': self.get_host_migrate_steps_cleaning_up()
        }]


class RedisNoPersistence(RedisSingle):
    pass


class RedisSentinelNoPersistence(RedisSentinel):
    pass


class RedisCluster(BaseRedis):

    def deploy_instances(self):
        return [
            [InstanceDeploy(Instance.REDIS, 6379)],
            [InstanceDeploy(Instance.REDIS, 6379)],
            [InstanceDeploy(Instance.REDIS, 6379)],
            [InstanceDeploy(Instance.REDIS, 6379)],
            [InstanceDeploy(Instance.REDIS, 6379)],
            [InstanceDeploy(Instance.REDIS, 6379)],
        ]

    def get_deploy_steps(self):
        return [{
            'Creating virtual machine': (
                'workflow.steps.util.host_provider.CreateVirtualMachine',
            )}, {
            'Creating dns': (
                'workflow.steps.util.dns.CreateDNS',
            )}, {
            'Creating disk': (
                'workflow.steps.util.volume_provider.NewVolume',
            )}, {
            'Waiting VMs': (
                'workflow.steps.util.vm.WaitingBeReady',
                'workflow.steps.util.vm.UpdateOSDescription'
            )}, {
            'Configuring database': (
                'workflow.steps.util.volume_provider.MountDataVolume',
                'workflow.steps.util.plan.InitializationForNewInfra',
                'workflow.steps.util.plan.ConfigureForNewInfra',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.metric_collector.RestartTelegraf',
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
            'Check ACL': (
                'workflow.steps.util.acl.BindNewInstance',
            )}, {
            'Creating monitoring and alarms': (
                'workflow.steps.util.zabbix.CreateAlarms',
                'workflow.steps.util.db_monitor.CreateInfraMonitoring',
            )
        }]

    def get_restore_snapshot_steps(self):
        return [{
            'Disable monitoring': (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
            )}, {
            'Restoring': (
                'workflow.steps.util.volume_provider.RestoreSnapshot',
            )}, {
            'Stopping datbase': (
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.CheckIsDown',
                'workflow.steps.redis.cluster.SaveNodeConfig'
            )}, {
            'Configuring': (
                'workflow.steps.util.volume_provider.AddAccessRestoredVolume',
                'workflow.steps.util.volume_provider.UnmountActiveVolume',
                'workflow.steps.util.volume_provider.MountDataVolumeRestored',
                'workflow.steps.util.disk.CleanData',
                'workflow.steps.util.disk.RemoveDeprecatedFiles',
                'workflow.steps.util.plan.ConfigureRestore',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
                'workflow.steps.redis.cluster.RestoreNodeConfig'
            )}, {
            'Starting database': (
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.metric_collector.RestartTelegraf',
            )}, {
            'Old data': (
                'workflow.steps.util.volume_provider.TakeSnapshot',
                'workflow.steps.util.volume_provider.UpdateActiveDisk',
            )}, {
            'Enabling monitoring': (
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
            )
        }]

    def get_host_migrate_steps_cleaning_up(self):
        return (
            'workflow.steps.redis.cluster.RemoveNode',
            'workflow.steps.redis.cluster.CheckClusterStatus',
            'workflow.steps.util.volume_provider.DestroyOldEnvironment',
            'workflow.steps.util.host_provider.DestroyVirtualMachineMigrate',
        )

    def get_base_host_migrate_steps(self):
        return (
            'workflow.steps.util.vm.ChangeMaster',
            'workflow.steps.util.database.CheckIfSwitchMaster',
            'workflow.steps.util.host_provider.CreateVirtualMachineMigrate',
            'workflow.steps.util.volume_provider.NewVolume',
            'workflow.steps.util.vm.WaitingBeReady',
            'workflow.steps.util.vm.UpdateOSDescription',
            'workflow.steps.util.volume_provider.MountDataVolume',
            'workflow.steps.util.plan.Initialization',
            'workflow.steps.util.plan.Configure',
            'workflow.steps.util.database.Start',
            'workflow.steps.util.database.CheckIsUp',
            'workflow.steps.util.vm.CheckAccessToMaster',
            'workflow.steps.util.vm.CheckAccessFromMaster',
            'workflow.steps.util.acl.ReplicateAclsMigrate',
            'workflow.steps.redis.cluster.AddSlaveNode',
            'workflow.steps.redis.horizontal_elasticity.database.SetNotEligible',
            'workflow.steps.redis.cluster.CheckClusterStatus',
            'workflow.steps.util.metric_collector.ConfigureTelegraf',
            'workflow.steps.util.metric_collector.RestartTelegraf',
            'workflow.steps.util.zabbix.DestroyAlarms',
            'workflow.steps.util.dns.ChangeEndpoint',
            'workflow.steps.util.dns.CheckIsReady',
            'workflow.steps.util.zabbix.CreateAlarms',
            'workflow.steps.util.disk.ChangeSnapshotOwner',
        )

    def get_host_migrate_steps(self):
        return [{
            'Migrating':
                self.get_base_host_migrate_steps() +
                self.get_host_migrate_steps_cleaning_up()
        }]

    def get_database_migrate_steps(self):
        return [{
            'Migrating': self.get_base_host_migrate_steps()
        }, {
            'Cleaning up': self.get_host_migrate_steps_cleaning_up()
        }]

    @property
    def driver_name(self):
        return 'redis_cluster'
