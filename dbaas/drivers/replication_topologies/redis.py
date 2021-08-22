# -*- coding: utf-8 -*-
from base import BaseTopology, InstanceDeploy
from physical.models import Instance


class BaseRedis(BaseTopology):
    def get_upgrade_steps_extra(self):
        return (
            'workflow.steps.util.volume_provider.AttachDataVolume',
            'workflow.steps.util.volume_provider.MountDataVolume',
            'workflow.steps.util.plan.InitializationForUpgrade',
            'workflow.steps.util.plan.ConfigureForUpgrade',
            'workflow.steps.util.plan.ConfigureLog',
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

    def get_change_binaries_upgrade_patch_steps(self):
        return (
            'workflow.steps.util.database_upgrade_patch.RedisCHGBinStep',
        )

    def get_change_binaries_upgrade_patch_steps_rollback(self):
        return (
            'workflow.steps.util.database_upgrade_patch.RedisCHGBinStepRollback',
        )

    def get_database_change_persistence_steps(self):
        return [{
            'Disable monitoring': (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
            )}, {
            'Change Database Persistence': (
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.CheckIfSwitchMaster',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.CheckIsDown',
                'workflow.steps.util.plan.ConfigureForChangePersistence',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.metric_collector.RestartTelegraf',
            )}, {
            'Enabling monitoring': (
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
            )
        }]

class RedisSingle(BaseRedis):

    @property
    def driver_name(self):
        return 'redis_single'

    def deploy_instances(self):
        return [[InstanceDeploy(Instance.REDIS, 6379)]]

    def get_deploy_steps(self):
        return [{
            'Creating Service Account': (
                'workflow.steps.util.host_provider.CreateServiceAccount',
            )}, {
            'Creating virtual machine': (
                'workflow.steps.util.host_provider.AllocateIP',
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
                'workflow.steps.util.volume_provider.AttachDataVolumeWithUndo',
                'workflow.steps.util.volume_provider.MountDataVolume',
                'workflow.steps.util.plan.InitializationForNewInfra',
                'workflow.steps.util.plan.ConfigureForNewInfra',
                'workflow.steps.util.plan.ConfigureLogForNewInfra',
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
            )}, {
            'Create Extra DNS': (
                'workflow.steps.util.database.CreateExtraDNS',
            )}, {
            'Update Host Disk Size': (
                'workflow.steps.util.host_provider.UpdateHostRootVolumeSize',
            )
        }]

    def get_clone_steps(self):
        return [{
            'Creating Service Account': (
                'workflow.steps.util.host_provider.CreateServiceAccount',
            )}, {
            'Creating virtual machine': (
                'workflow.steps.util.host_provider.AllocateIP',
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
                'workflow.steps.util.volume_provider.AttachDataVolume',
                'workflow.steps.util.volume_provider.MountDataVolume',
                'workflow.steps.util.plan.InitializationForNewInfra',
                'workflow.steps.util.plan.ConfigureForNewInfra',
                'workflow.steps.util.plan.ConfigureLogForNewInfra',
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
                'workflow.steps.util.database.Clone',
                'workflow.steps.util.clone.clone_database.CloneDatabaseData'
            )}, {
            'Check ACL': (
                'workflow.steps.util.acl.BindNewInstance',
            )}, {
            'Creating monitoring and alarms': (
                'workflow.steps.util.zabbix.CreateAlarms',
                'workflow.steps.util.db_monitor.CreateInfraMonitoring',
            )}, {
            'Create Extra DNS': (
                'workflow.steps.util.database.CreateExtraDNS',
            )}, {
            'Update Host Disk Size': (
                'workflow.steps.util.host_provider.UpdateHostRootVolumeSize',
            )
        }]

    '''
    def get_host_migrate_steps(self):
        return [{
            'Migrating': (
                'workflow.steps.util.host_provider.CreateVirtualMachineMigrate',
                'workflow.steps.util.volume_provider.NewVolume',
                'workflow.steps.util.vm.WaitingBeReady',
                'workflow.steps.util.vm.UpdateOSDescription',
                'workflow.steps.util.host_provider.UpdateHostRootVolumeSize',
                'workflow.steps.util.volume_provider.AttachDataVolume',
                'workflow.steps.util.volume_provider.MountDataVolume',
                'workflow.steps.util.plan.Initialization',
                'workflow.steps.util.plan.Configure',
                'workflow.steps.util.plan.ConfigureLog',
                ) + self.get_change_binaries_upgrade_patch_steps() + (
                'workflow.steps.util.volume_provider.TakeSnapshotFromMaster',
                ('workflow.steps.util.volume_provider'
                 '.WaitSnapshotAvailableMigrate'),
                'workflow.steps.util.disk.CleanDataRecreateSlave',
                'workflow.steps.util.volume_provider.AddAccessRecreateSlave',
                ('workflow.steps.util.volume_provider'
                 '.MountDataVolumeRecreateSlave'),
                'workflow.steps.util.volume_provider.CopyDataFromSnapShot',
                'workflow.steps.util.volume_provider.DetachDataVolumeRecreateSlave',
                ('workflow.steps.util.volume_provider'
                 '.UmountDataVolumeRecreateSlave'),
                ('workflow.steps.util.volume_provider'
                 '.RemoveAccessRecreateSlave'),
                'workflow.steps.util.volume_provider.RemoveSnapshotMigrate',
                'workflow.steps.util.disk.RemoveDeprecatedFiles',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.acl.ReplicateAclsMigrate',
                'workflow.steps.util.zabbix.DestroyAlarms',
                'workflow.steps.util.dns.ChangeEndpoint',
                'workflow.steps.util.dns.CheckIsReady',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
                'workflow.steps.util.metric_collector.RestartTelegraf',
                'workflow.steps.util.zabbix.CreateAlarms',
                'workflow.steps.util.disk.ChangeSnapshotOwner',
            )
        }, {
            'Cleaning up': (
                'workflow.steps.util.volume_provider.DestroyOldEnvironment',
                'workflow.steps.util.host_provider.DestroyVirtualMachineMigrate',
            )
        }]
    '''

    def get_base_host_migrate_steps(self):
        return (
            'workflow.steps.util.host_provider.CreateVirtualMachineMigrate',
            'workflow.steps.util.volume_provider.NewVolume',
            'workflow.steps.util.vm.WaitingBeReady',
            'workflow.steps.util.vm.UpdateOSDescription',
            'workflow.steps.util.host_provider.UpdateHostRootVolumeSize',
            'workflow.steps.util.volume_provider.AttachDataVolume',
            'workflow.steps.util.volume_provider.MountDataVolume',
            'workflow.steps.util.plan.Initialization',
            'workflow.steps.util.plan.Configure',
            'workflow.steps.util.plan.ConfigureLog',
            ) + self.get_change_binaries_upgrade_patch_steps() + (
            'workflow.steps.util.volume_provider.TakeSnapshotFromMaster',
            ('workflow.steps.util.volume_provider'
             '.WaitSnapshotAvailableMigrate'),
            'workflow.steps.util.disk.CleanDataRecreateSlave',
            'workflow.steps.util.volume_provider.AddAccessRecreateSlave',
            ('workflow.steps.util.volume_provider'
             '.MountDataVolumeRecreateSlave'),
            'workflow.steps.util.volume_provider.CopyDataFromSnapShot',
            'workflow.steps.util.volume_provider.DetachDataVolumeRecreateSlave',
            ('workflow.steps.util.volume_provider'
             '.UmountDataVolumeRecreateSlave'),
            ('workflow.steps.util.volume_provider'
             '.RemoveAccessRecreateSlave'),
            'workflow.steps.util.volume_provider.RemoveSnapshotMigrate',
            'workflow.steps.util.disk.RemoveDeprecatedFiles',
            'workflow.steps.util.database.Start',
            'workflow.steps.util.database.CheckIsUp',
            'workflow.steps.util.acl.ReplicateAclsMigrate',
            'workflow.steps.util.zabbix.DestroyAlarms',
            'workflow.steps.util.dns.ChangeEndpoint',
            'workflow.steps.util.dns.CheckIsReady',
            'workflow.steps.util.metric_collector.ConfigureTelegraf',
            'workflow.steps.util.metric_collector.RestartTelegraf',
            'workflow.steps.util.zabbix.CreateAlarms',
            'workflow.steps.util.disk.ChangeSnapshotOwner',
            )

    def get_host_migrate_steps_cleaning_up(self):
        return (
            'workflow.steps.util.volume_provider.DestroyOldEnvironment',
            'workflow.steps.util.host_provider.DestroyVirtualMachineMigrate',
        )

    def get_host_migrate_steps(self):
        return [{
            'Migrating':
                self.get_base_host_migrate_steps() +
                self.get_host_migrate_steps_cleaning_up()
        }]

    def get_filer_migrate_steps(self):
        return [{
            'Migrating': (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
                'workflow.steps.util.volume_provider.NewInactiveVolume',
                'workflow.steps.util.metric_collector.StopTelegraf',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.StopRsyslog',
                'workflow.steps.util.database.CheckIsDown',
                'workflow.steps.util.volume_provider.AddAccessNewVolume',
                'workflow.steps.util.volume_provider.MountDataLatestVolume',
                'workflow.steps.util.volume_provider.CopyPermissions',
                'workflow.steps.util.volume_provider.CopyFiles',
                'workflow.steps.util.volume_provider.UnmountDataLatestVolume',
                'workflow.steps.util.volume_provider.DetachDataVolume',
                'workflow.steps.util.volume_provider.UnmountDataVolume',
                'workflow.steps.util.volume_provider.MountDataNewVolume',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.StartRsyslog',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.metric_collector.RestartTelegraf',
                'workflow.steps.util.volume_provider.TakeSnapshotOldDisk',
                'workflow.steps.util.volume_provider.UpdateActiveDisk',
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
            )}
        ]

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
                'workflow.steps.util.database.StopRsyslog',
                'workflow.steps.util.database.CheckIsDown',
            )}, {
            'Configuring': (
                'workflow.steps.util.volume_provider.AddAccessRestoredVolume',
                'workflow.steps.util.volume_provider.UnmountActiveVolume',
                'workflow.steps.util.volume_provider.AttachDataVolumeRestored',
                'workflow.steps.util.volume_provider.MountDataVolumeRestored',
                'workflow.steps.util.plan.ConfigureRestore',
                'workflow.steps.util.plan.ConfigureLog',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
            )}, {
            'Starting database': (
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.StartRsyslog',
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

    @property
    def driver_name(self):
        return 'redis_sentinel'

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
            'workflow.steps.util.volume_provider.AttachDataVolume',
            'workflow.steps.util.volume_provider.MountDataVolume',
            'workflow.steps.util.plan.Initialization',
            'workflow.steps.util.plan.Configure',
            'workflow.steps.util.plan.ConfigureLog',
            'workflow.steps.util.metric_collector.ConfigureTelegraf'
            ) + self.get_change_binaries_upgrade_patch_steps() + (
            'workflow.steps.util.database.Start',
            'workflow.steps.util.metric_collector.RestartTelegraf',
            'workflow.steps.redis.horizontal_elasticity.database.AddInstanceToRedisCluster',
        )

    def get_filer_migrate_steps(self):
        return [{
            'Migrating': (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.CheckIfSwitchMaster',
                'workflow.steps.util.volume_provider.NewInactiveVolume',
                'workflow.steps.util.metric_collector.StopTelegraf',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.StopRsyslog',
                'workflow.steps.util.database.CheckIsDown',
                'workflow.steps.util.volume_provider.AddAccessNewVolume',
                'workflow.steps.util.volume_provider.MountDataLatestVolume',
                'workflow.steps.util.volume_provider.CopyPermissions',
                'workflow.steps.util.volume_provider.CopyFiles',
                'workflow.steps.util.volume_provider.UnmountDataLatestVolume',
                'workflow.steps.util.volume_provider.DetachDataVolume',
                'workflow.steps.util.volume_provider.UnmountDataVolume',
                'workflow.steps.util.volume_provider.MountDataNewVolume',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.StartRsyslog',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.database.WaitForReplication',
                'workflow.steps.util.metric_collector.RestartTelegraf',
                'workflow.steps.util.volume_provider.TakeSnapshotOldDisk',
                'workflow.steps.util.volume_provider.UpdateActiveDisk',
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
            )}
        ]

    def get_restore_snapshot_steps(self):
        return [{
            'Disable monitoring': (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
            )}, {
            'Restoring': (
                'workflow.steps.util.volume_provider.RestoreSnapshotToMaster',
            )}, {
            'Stopping datbase': (
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.StopRsyslog',
                'workflow.steps.util.database.CheckIsDown',
            )}, {
            'Configuring': (
                'workflow.steps.util.volume_provider.AddAccessRestoredVolume',
                'workflow.steps.util.volume_provider.UnmountActiveVolume',
                'workflow.steps.util.volume_provider.MoveDiskRestore',
                'workflow.steps.util.volume_provider.AttachDataVolumeRestored',
                'workflow.steps.util.volume_provider.MountDataVolumeRestored',
                'workflow.steps.util.disk.CleanData',
                'workflow.steps.util.disk.RemoveDeprecatedFiles',
                'workflow.steps.util.plan.ConfigureRestore',
                'workflow.steps.util.plan.ConfigureLog',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
            )}, {
            'Starting database': (
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.StartRsyslog',
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
            'Creating Service Account': (
                'workflow.steps.util.host_provider.CreateServiceAccount',
            )}, {
            'Creating virtual machine': (
                'workflow.steps.util.host_provider.AllocateIP',
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
                'workflow.steps.util.volume_provider.AttachDataVolumeWithUndo',
                'workflow.steps.util.volume_provider.MountDataVolume',
                'workflow.steps.util.plan.InitializationForNewInfraSentinel',
                'workflow.steps.util.plan.ConfigureForNewInfraSentinel',
                'workflow.steps.util.plan.ConfigureLogForNewInfra',
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
            )}, {
            'Create Extra DNS': (
                'workflow.steps.util.database.CreateExtraDNS',
            )}, {
            'Update Host Disk Size': (
                'workflow.steps.util.host_provider.UpdateHostRootVolumeSize',
            )
        }]

    def get_clone_steps(self):
        return [{
            'Creating Service Account': (
                'workflow.steps.util.host_provider.CreateServiceAccount',
            )}, {
            'Creating virtual machine': (
                'workflow.steps.util.host_provider.AllocateIP',
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
                'workflow.steps.util.volume_provider.AttachDataVolume',
                'workflow.steps.util.volume_provider.MountDataVolume',
                'workflow.steps.util.plan.InitializationForNewInfraSentinel',
                'workflow.steps.util.plan.ConfigureForNewInfraSentinel',
                'workflow.steps.util.plan.ConfigureLogForNewInfra',
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
                'workflow.steps.util.database.Clone',
                'workflow.steps.util.clone.clone_database.CloneDatabaseData'
            )}, {
            'Check ACL': (
                'workflow.steps.util.acl.BindNewInstance',
            )}, {
            'Creating monitoring and alarms': (
                'workflow.steps.util.sentinel.CreateAlarmsNewInfra',
                'workflow.steps.util.db_monitor.CreateInfraMonitoring',
            )}, {
            'Create Extra DNS': (
                'workflow.steps.util.database.CreateExtraDNS',
            )}, {
            'Update Host Disk Size': (
                'workflow.steps.util.host_provider.UpdateHostRootVolumeSize',
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
            'workflow.steps.util.host_provider.UpdateHostRootVolumeSize',
            'workflow.steps.util.volume_provider.AttachDataVolume',
            'workflow.steps.util.volume_provider.MountDataVolume',
            'workflow.steps.util.plan.Initialization',
            'workflow.steps.util.plan.Configure',
            'workflow.steps.util.plan.ConfigureLog',
            ) + self.get_change_binaries_upgrade_patch_steps() + (
            'workflow.steps.util.database.Start',
            'workflow.steps.util.database.CheckIsUp',
            'workflow.steps.util.vm.CheckAccessToMaster',
            'workflow.steps.util.vm.CheckAccessFromMaster',
            'workflow.steps.util.acl.ReplicateAclsMigrate',
            'workflow.steps.redis.upgrade.sentinel.ResetAllSentinel',
            'workflow.steps.util.database.SetSlave',
            'workflow.steps.util.database.WaitForReplication',
            'workflow.steps.redis.horizontal_elasticity.database.SetNotEligible',
            'workflow.steps.util.zabbix.DestroyAlarms',
            'workflow.steps.util.dns.ChangeEndpoint',
            'workflow.steps.util.dns.CheckIsReady',
            'workflow.steps.util.metric_collector.ConfigureTelegraf',
            'workflow.steps.util.metric_collector.RestartTelegraf',
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

    def get_database_migrate_steps_stage_1(self):
        return [{
            'Creating Service Account': (
                'workflow.steps.util.host_provider.CreateServiceAccount',
            )}, {
            'Creating virtual machine': (
                'workflow.steps.util.host_provider.AllocateIP',
                'workflow.steps.util.host_provider.CreateVirtualMachineMigrate',
            )}, {
            'Creating disk': (
                'workflow.steps.util.volume_provider.NewVolume',
            )}, {
            'Waiting VMs': (
                'workflow.steps.util.vm.WaitingBeReady',
                'workflow.steps.util.vm.UpdateOSDescription',
                'workflow.steps.util.host_provider.UpdateHostRootVolumeSize',
            )}, {
            'Check patch': (
                ) + self.get_change_binaries_upgrade_patch_steps() + (
            )}, {
            'Configuring database': (
                'workflow.steps.util.volume_provider.AttachDataVolume',
                'workflow.steps.util.volume_provider.MountDataVolume',
                'workflow.steps.util.plan.Initialization',
            )}, {
            #'Backup and restore': (
            #    'workflow.steps.util.volume_provider.TakeSnapshotMigrate',
            #    'workflow.steps.util.volume_provider.WaitSnapshotAvailableMigrate',
            #    'workflow.steps.util.volume_provider.AddHostsAllowMigrate',
            #    'workflow.steps.util.volume_provider.CreatePubKeyMigrate',
            #    'workflow.steps.util.database.StopWithoutUndo',
            #    'workflow.steps.util.database.CheckIsDown',
            #    'workflow.steps.util.disk.CleanDataMigrate',
            #    'workflow.steps.util.volume_provider.RsyncFromSnapshotMigrate',
            #    'workflow.steps.util.volume_provider.RemovePubKeyMigrate',
            #    'workflow.steps.util.volume_provider.RemoveHostsAllowMigrate',
            #)}, {
            'Configure SSL lib and folder': (
                ) + self.get_configure_ssl_libs_and_folder_steps() + (
            )}, {
            'Configure SSL (IP)': (
                ) + self.get_configure_ssl_ip_steps() + (
            )}, {
            'Configure and start database': (
            #    'workflow.steps.util.disk.RemoveDeprecatedFiles',
                'workflow.steps.util.plan.Configure',
                'workflow.steps.util.plan.ConfigureLog',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
            )}, {
            'Check access between instances': (
                'workflow.steps.util.vm.CheckAccessToMaster',
                'workflow.steps.util.vm.CheckAccessFromMaster',
            )}, {
            'Replicate ACL': (
                'workflow.steps.util.acl.ReplicateAclsMigrate',
                'workflow.steps.util.acl.BindNewInstance',
            )}, {
            'Configure replication': (
                'workflow.steps.redis.upgrade.sentinel.ResetAllSentinel',
                'workflow.steps.util.database.SetSlave',
                'workflow.steps.util.database.WaitForReplication',
                'workflow.steps.redis.horizontal_elasticity.database.SetNotEligible',
            )}, {
            #'Stopping database': (
            #    'workflow.steps.util.database.Stop',
            #    'workflow.steps.util.database.StopRsyslog',
            #    'workflow.steps.util.database.CheckIsDown',
            #)}, {
            #'Destroy Alarms': (
            #    'workflow.steps.util.zabbix.DestroyAlarms',
            #)}, {
            #'Update and Check DNS': (
            #    'workflow.steps.util.dns.ChangeEndpoint',
            #    'workflow.steps.util.dns.CheckIsReady',
            #)}, {
            #'Configure SSL (DNS)': (
            #    ) + self.get_configure_ssl_dns_steps() + (
            #)}, {
            #'Starting database': (
            #    'workflow.steps.util.database.Start',
            #    'workflow.steps.util.database.CheckIsUp',
            #    'workflow.steps.util.database.StartRsyslog',
            #    'workflow.steps.util.metric_collector.ConfigureTelegraf',
            #    'workflow.steps.util.metric_collector.RestartTelegraf',
            #    'workflow.steps.util.disk.ChangeSnapshotOwner',
            #)}, {
            #'Recreate Alarms': (
            #    'workflow.steps.util.zabbix.CreateAlarms',
            #    'workflow.steps.util.db_monitor.UpdateInfraCloudDatabaseMigrate',
            #)}, {
            'Raise Test Migrate Exception': (
                'workflow.steps.util.base.BaseRaiseTestException',
        )}]
class RedisNoPersistence(RedisSingle):
    pass


class RedisSentinelNoPersistence(RedisSentinel):
    pass


class RedisCluster(BaseRedis):

    @property
    def driver_name(self):
        return 'redis_cluster'

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
            'Creating Service Account': (
                'workflow.steps.util.host_provider.CreateServiceAccount',
            )}, {
            'Creating virtual machine': (
                'workflow.steps.util.host_provider.AllocateIP',
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
                'workflow.steps.util.volume_provider.AttachDataVolumeWithUndo',
                'workflow.steps.util.volume_provider.MountDataVolume',
                'workflow.steps.util.plan.InitializationForNewInfra',
                'workflow.steps.util.plan.ConfigureForNewInfra',
                'workflow.steps.util.plan.ConfigureLogForNewInfra',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.metric_collector.RestartTelegraf',
            )}, {
            'Configuring Cluster': (
                'workflow.steps.redis.cluster.CreateCluster',
                'workflow.steps.redis.cluster.CheckClusterStatus',
                'workflow.steps.redis.cluster.CreateClusterRedisAddSlaves',
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
            )}, {
            'Create Extra DNS': (
                'workflow.steps.util.database.CreateExtraDNS',
            )}, {
            'Update Host Disk Size': (
                'workflow.steps.util.host_provider.UpdateHostRootVolumeSize',
            )
        }]

    def get_filer_migrate_steps(self):
        return [{
            'Migrating': (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.CheckIfSwitchMaster',
                'workflow.steps.util.volume_provider.NewInactiveVolume',
                'workflow.steps.util.metric_collector.StopTelegraf',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.StopRsyslog',
                'workflow.steps.util.database.CheckIsDown',
                'workflow.steps.util.volume_provider.AddAccessNewVolume',
                'workflow.steps.util.volume_provider.MountDataLatestVolume',
                'workflow.steps.util.volume_provider.CopyPermissions',
                'workflow.steps.util.volume_provider.CopyFiles',
                'workflow.steps.util.volume_provider.UnmountDataLatestVolume',
                'workflow.steps.util.volume_provider.DetachDataVolume',
                'workflow.steps.util.volume_provider.UnmountDataVolume',
                'workflow.steps.util.volume_provider.MountDataNewVolume',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.StartRsyslog',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.database.WaitForReplication',
                'workflow.steps.util.metric_collector.RestartTelegraf',
                'workflow.steps.util.volume_provider.TakeSnapshotOldDisk',
                'workflow.steps.util.volume_provider.UpdateActiveDisk',
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
            )}
        ]

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
                'workflow.steps.util.database.StopRsyslog',
                'workflow.steps.util.database.CheckIsDown',
                'workflow.steps.redis.cluster.SaveNodeConfig'
            )}, {
            'Configuring': (
                'workflow.steps.util.volume_provider.AddAccessRestoredVolume',
                'workflow.steps.util.volume_provider.UnmountActiveVolume',
                'workflow.steps.util.volume_provider.MoveDiskRestore',
                'workflow.steps.util.volume_provider.AttachDataVolumeRestored',
                'workflow.steps.util.volume_provider.MountDataVolumeRestored',
                'workflow.steps.util.disk.CleanData',
                'workflow.steps.util.disk.RemoveDeprecatedFiles',
                'workflow.steps.util.plan.ConfigureRestore',
                'workflow.steps.util.plan.ConfigureLog',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
                'workflow.steps.redis.cluster.RestoreNodeConfig'
            )}, {
            'Starting database': (
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.StartRsyslog',
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
            'workflow.steps.util.host_provider.UpdateHostRootVolumeSize',
            'workflow.steps.util.volume_provider.AttachDataVolume',
            'workflow.steps.util.volume_provider.MountDataVolume',
            'workflow.steps.util.plan.Initialization',
            'workflow.steps.util.plan.Configure',
                'workflow.steps.util.plan.ConfigureLog',
            ) + self.get_change_binaries_upgrade_patch_steps() + (
            'workflow.steps.util.database.Start',
            'workflow.steps.util.database.CheckIsUp',
            'workflow.steps.util.vm.CheckAccessToMaster',
            'workflow.steps.util.vm.CheckAccessFromMaster',
            'workflow.steps.util.acl.ReplicateAclsMigrate',
            'workflow.steps.redis.cluster.AddSlaveNode',
            'workflow.steps.redis.horizontal_elasticity.database.SetNotEligible',
            'workflow.steps.redis.cluster.CheckClusterStatus',
            'workflow.steps.util.zabbix.DestroyAlarms',
            'workflow.steps.util.dns.ChangeEndpoint',
            'workflow.steps.util.dns.CheckIsReady',
            'workflow.steps.util.metric_collector.ConfigureTelegraf',
            'workflow.steps.util.metric_collector.RestartTelegraf',
            'workflow.steps.util.zabbix.CreateAlarms',
            'workflow.steps.util.db_monitor.UpdateInfraCloudDatabaseMigrate',
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


class RedisGenericGCE(object):
    def get_single_host_migrate_steps(self):
        return [{
            'Disable monitoring and alarms': (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
            )}, {
            'Stop previous database': (
                'workflow.steps.util.metric_collector.RestartTelegrafRollback',
                'workflow.steps.util.metric_collector.ConfigureTelegrafRollback',
                'workflow.steps.util.database.CheckIsUpRollback',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.StopRsyslog',
                'workflow.steps.util.database.CheckIsDown',
            )}, {
            'Check patch if rollback': (
                ) + self.get_change_binaries_upgrade_patch_steps_rollback() + (
            )}, {
            'Configure if rollback': (
                'workflow.steps.util.plan.ConfigureLogRollback',
                'workflow.steps.util.plan.ConfigureRollback',
            )}, {
            'Remove previous VM': (
                'workflow.steps.util.volume_provider.DetachDataVolume',
                'workflow.steps.util.vm.WaitingBeReadyRollback',
                'workflow.steps.util.host_provider.DestroyVirtualMachineMigrateKeepObject'
            )}, {
            'Create new VM': (
                'workflow.steps.util.host_provider.RecreateVirtualMachineMigrate',
            )}, {
            'Configure instance': (
                'workflow.steps.util.volume_provider.MoveDisk',
                'workflow.steps.util.volume_provider.AttachDataVolumeWithUndo',
                'workflow.steps.util.volume_provider.MountDataVolumeWithUndo',
                'workflow.steps.util.plan.Configure',
                'workflow.steps.util.plan.ConfigureLog',
            )}, {
            'Check patch': (
                ) + self.get_change_binaries_upgrade_patch_steps() + (
            )}, {
            'Starting database': (
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.database.StartRsyslog',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
                'workflow.steps.util.metric_collector.RestartTelegraf',
            )}, {
            'Enabling monitoring and alarms': (
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
            )}
        ]


    def get_sentinel_host_migrate_steps(self):
        return [{
            'Disable monitoring and alarms': (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
            )}, {
            'Stop pevious database': (
                'workflow.steps.util.metric_collector.RestartTelegrafRollback',
                'workflow.steps.util.metric_collector.ConfigureTelegrafRollback',
                'workflow.steps.util.database.CheckIsUpRollback',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.StopRsyslog',
                'workflow.steps.util.database.CheckIsDown',
            )}, {
            'Check patch if rollback': (
                ) + self.get_change_binaries_upgrade_patch_steps_rollback() + (
            )}, {
            'Configure if rollback': (
                'workflow.steps.util.plan.ConfigureLogRollback',
                'workflow.steps.util.plan.ConfigureRollback',
                'workflow.steps.util.plan.InitializationMigrateRollback',
            )}, {
            'Remove previous VM': (
                'workflow.steps.util.volume_provider.DetachDataVolume',
                'workflow.steps.util.vm.WaitingBeReadyRollback',
                'workflow.steps.util.host_provider.DestroyVirtualMachineMigrateKeepObject'
            )}, {
            'Create new VM': (
                'workflow.steps.util.host_provider.RecreateVirtualMachineMigrate',
            )}, {
            'Configure instance': (
                'workflow.steps.util.volume_provider.MoveDisk',
                'workflow.steps.util.volume_provider.AttachDataVolumeWithUndo',
                'workflow.steps.util.volume_provider.MountDataVolumeWithUndo',
                'workflow.steps.util.vm.WaitingBeReady',
                'workflow.steps.util.plan.InitializationMigrate',
                'workflow.steps.util.plan.Configure',
                'workflow.steps.util.plan.ConfigureLog',
            )}, {
            'Check patch': (
                ) + self.get_change_binaries_upgrade_patch_steps() + (
            )}, {
            'Starting database': (
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.database.StartRsyslog',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
                'workflow.steps.util.metric_collector.RestartTelegraf',
                'workflow.steps.redis.upgrade.sentinel.ResetAllSentinel',
                'workflow.steps.util.database.SetSlave',
                'workflow.steps.util.database.WaitForReplication',
            )}, {
            'Enabling monitoring and alarms': (
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
            )}
        ]

        '''
        return (
            'workflow.steps.util.vm.ChangeMaster',
            'workflow.steps.util.database.CheckIfSwitchMaster',
            'workflow.steps.util.host_provider.CreateVirtualMachineMigrate',
            'workflow.steps.util.volume_provider.NewVolume',
            'workflow.steps.util.vm.WaitingBeReady',
            'workflow.steps.util.vm.UpdateOSDescription',
            'workflow.steps.util.host_provider.UpdateHostRootVolumeSize',
            'workflow.steps.util.volume_provider.AttachDataVolume',
            'workflow.steps.util.volume_provider.MountDataVolume',
            'workflow.steps.util.plan.Initialization',
            'workflow.steps.util.plan.Configure',
            'workflow.steps.util.plan.ConfigureLog',
            ) + self.get_change_binaries_upgrade_patch_steps() + (
            'workflow.steps.util.database.Start',
            'workflow.steps.util.database.CheckIsUp',
            'workflow.steps.util.vm.CheckAccessToMaster',
            'workflow.steps.util.vm.CheckAccessFromMaster',
            'workflow.steps.util.acl.ReplicateAclsMigrate',
            'workflow.steps.redis.upgrade.sentinel.ResetAllSentinel',
            'workflow.steps.util.database.SetSlave',
            'workflow.steps.util.database.WaitForReplication',
            'workflow.steps.redis.horizontal_elasticity.database.SetNotEligible',
            'workflow.steps.util.zabbix.DestroyAlarms',
            'workflow.steps.util.dns.ChangeEndpoint',
            'workflow.steps.util.dns.CheckIsReady',
            'workflow.steps.util.metric_collector.ConfigureTelegraf',
            'workflow.steps.util.metric_collector.RestartTelegraf',
            'workflow.steps.util.zabbix.CreateAlarms',
            'workflow.steps.util.disk.ChangeSnapshotOwner',
        )
        '''

    def get_cluster_host_migrate_steps(self):
        return [{
            'Disable monitoring and alarms': (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
            )}, {
            'Stop pevious database': (
                'workflow.steps.util.metric_collector.RestartTelegrafRollback',
                'workflow.steps.util.metric_collector.ConfigureTelegrafRollback',
                'workflow.steps.util.database.CheckIsUpRollback',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.StopRsyslog',
                'workflow.steps.util.database.CheckIsDown',
            )}, {
            'Check patch if rollback': (
                ) + self.get_change_binaries_upgrade_patch_steps_rollback() + (
            )}, {
            'Configure if rollback': (
                'workflow.steps.util.plan.ConfigureLogRollback',
                'workflow.steps.util.plan.ConfigureRollback',
                'workflow.steps.util.plan.InitializationMigrateRollback',
            )}, {
            'Remove previous VM': (
                'workflow.steps.util.volume_provider.DetachDataVolume',
                'workflow.steps.util.vm.WaitingBeReadyRollback',
                'workflow.steps.util.host_provider.DestroyVirtualMachineMigrateKeepObject'
            )}, {
            'Create new VM': (
                'workflow.steps.util.host_provider.RecreateVirtualMachineMigrate',
            )}, {
            'Configure instance': (
                'workflow.steps.util.volume_provider.MoveDisk',
                'workflow.steps.util.volume_provider.AttachDataVolumeWithUndo',
                'workflow.steps.util.volume_provider.MountDataVolumeWithUndo',
                'workflow.steps.util.vm.WaitingBeReady',
                'workflow.steps.util.plan.InitializationMigrate',
                'workflow.steps.util.plan.Configure',
                'workflow.steps.util.plan.ConfigureLog',
            )}, {
            'Check patch': (
                ) + self.get_change_binaries_upgrade_patch_steps() + (
            )}, {
            'Starting database': (
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.database.StartRsyslog',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
                'workflow.steps.util.metric_collector.RestartTelegraf',
            )}, {
            'Enabling monitoring and alarms': (
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
            )}
        ]
        '''
        return (
            'workflow.steps.util.vm.ChangeMaster',
            'workflow.steps.util.database.CheckIfSwitchMaster',
            'workflow.steps.util.host_provider.CreateVirtualMachineMigrate',
            'workflow.steps.util.volume_provider.NewVolume',
            'workflow.steps.util.vm.WaitingBeReady',
            'workflow.steps.util.vm.UpdateOSDescription',
            'workflow.steps.util.host_provider.UpdateHostRootVolumeSize',
            'workflow.steps.util.volume_provider.AttachDataVolume',
            'workflow.steps.util.volume_provider.MountDataVolume',
            'workflow.steps.util.plan.Initialization',
            'workflow.steps.util.plan.Configure',
                'workflow.steps.util.plan.ConfigureLog',
            ) + self.get_change_binaries_upgrade_patch_steps() + (
            'workflow.steps.util.database.Start',
            'workflow.steps.util.database.CheckIsUp',
            'workflow.steps.util.vm.CheckAccessToMaster',
            'workflow.steps.util.vm.CheckAccessFromMaster',
            'workflow.steps.util.acl.ReplicateAclsMigrate',
            'workflow.steps.redis.cluster.AddSlaveNode',
            'workflow.steps.redis.horizontal_elasticity.database.SetNotEligible',
            'workflow.steps.redis.cluster.CheckClusterStatus',
            'workflow.steps.util.zabbix.DestroyAlarms',
            'workflow.steps.util.dns.ChangeEndpoint',
            'workflow.steps.util.dns.CheckIsReady',
            'workflow.steps.util.metric_collector.ConfigureTelegraf',
            'workflow.steps.util.metric_collector.RestartTelegraf',
            'workflow.steps.util.zabbix.CreateAlarms',
            'workflow.steps.util.db_monitor.UpdateInfraCloudDatabaseMigrate',
            'workflow.steps.util.disk.ChangeSnapshotOwner',
        )
        '''


class RedisSingleGCE(RedisSingle, RedisGenericGCE):
    def get_host_migrate_steps(self):
        return self.get_single_host_migrate_steps()

class RedisNoPersistenceGCE(RedisNoPersistence, RedisGenericGCE):
    def get_host_migrate_steps(self):
        return self.get_single_host_migrate_steps()

class RedisSentinelGCE(RedisSentinel, RedisGenericGCE):
    def get_host_migrate_steps(self):
        return self.get_sentinel_host_migrate_steps()

class RedisSentinelNoPersistenceGCE(RedisSentinelNoPersistence, RedisGenericGCE):
    def get_host_migrate_steps(self):
        return self.get_sentinel_host_migrate_steps()

class RedisClusterGCE(RedisCluster, RedisGenericGCE):
    def get_host_migrate_steps(self):
        return self.get_cluster_host_migrate_steps()
