# -*- coding: utf-8 -*-
class BaseTopology(object):

    @property
    def driver_name(self):
        raise NotImplementedError

    def deploy_instances(self):
        """ This method returns deploy instances to an infra. It must be
        implemented for every new type added to Instance Model, even subclasses
        of the existent ones."""
        raise NotImplementedError

    def deploy_first_steps(self):
        raise NotImplementedError()

    def deploy_last_steps(self):
        raise NotImplementedError()

    def monitoring_steps(self):
        return (
            'workflow.steps.util.deploy.create_zabbix.CreateZabbix',
            'workflow.steps.util.deploy.create_dbmonitor.CreateDbMonitor',
        )

    def get_deploy_steps(self):
        return self.deploy_first_steps() + self.monitoring_steps() + self.deploy_last_steps()

    def get_destroy_steps(self):
        return self.deploy_first_steps() + self.monitoring_steps() + self.deploy_last_steps()

    def get_clone_steps(self):
        raise NotImplementedError()

    def get_resize_extra_steps(self):
        return (
            'workflow.steps.util.database.Start',
            'workflow.steps.util.database.StartSlave',
            'workflow.steps.util.agents.Start',
            'workflow.steps.util.database.CheckIsUp',
            'workflow.steps.util.database.WaitForReplication',
        )

    def get_resize_steps(self):
        return [{'Resizing database': (
            'workflow.steps.util.zabbix.DisableAlarms',
            'workflow.steps.util.database.checkAndFixMySQLReplication',
            'workflow.steps.util.vm.ChangeMaster',
            'workflow.steps.util.database.CheckIfSwitchMaster',
            'workflow.steps.util.agents.Stop',
            'workflow.steps.util.database.StopSlave',
            'workflow.steps.util.database.StopRsyslog',
            'workflow.steps.util.database.Stop',
            'workflow.steps.util.plan.ResizeConfigure',
            'workflow.steps.util.plan.ConfigureLog',
            'workflow.steps.util.host_provider.Stop',
            'workflow.steps.util.host_provider.ChangeOffering',
            'workflow.steps.util.host_provider.Start',
            'workflow.steps.util.vm.WaitingBeReady',
        ) + self.get_resize_extra_steps() + (
            'workflow.steps.util.infra.Offering',
            'workflow.steps.util.vm.InstanceIsSlave',
            'workflow.steps.util.zabbix.EnableAlarms',
        )}]

    def get_upgrade_disk_type_steps(self):
        return [{
            'Upgrading disk type database': (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
                'workflow.steps.util.database.checkAndFixMySQLReplication',
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.CheckIfSwitchMaster',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.StopRsyslog',
                'workflow.steps.util.database.CheckIsDown',
                'workflow.steps.util.volume_provider.TakeSnapshotUpgradeDiskType',
                'workflow.steps.util.volume_provider.CreateVolumeDiskTypeUpgrade',
                'workflow.steps.util.volume_provider.AddAccessUpgradedDiskTypeVolume',
                'workflow.steps.util.volume_provider.UnmountActiveVolumeUpgradeDiskType',
                'workflow.steps.util.volume_provider.AttachDataVolumeUpgradeDiskType',
                'workflow.steps.util.volume_provider.MountDataVolumeUpgradeDiskType',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.StartRsyslog',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.volume_provider.UpdateActiveDiskTypeUpgrade',
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
            )}]

    def get_restore_snapshot_steps(self):
        raise NotImplementedError

    def get_upgrade_steps_initial_description(self):
        return 'Disable monitoring and alarms'

    def get_upgrade_steps_description(self):
        return 'Upgrading database'

    def get_upgrade_steps_final_description(self):
        return 'Enabling monitoring and alarms'

    def get_upgrade_steps(self):
        return [{
            self.get_upgrade_steps_initial_description(): (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
            ),
        }] + [{
            self.get_upgrade_steps_description(): (
                'workflow.steps.util.database.checkAndFixMySQLReplication',
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.CheckIfSwitchMaster',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.CheckIsDown',
                'workflow.steps.util.database.StopRsyslog',
                'workflow.steps.util.host_provider.Stop',
                'workflow.steps.util.volume_provider.DetachDataVolume',
                'workflow.steps.util.host_provider.InstallNewTemplate',
                'workflow.steps.util.host_provider.Start',
                'workflow.steps.util.vm.WaitingBeReady',
                'workflow.steps.util.vm.UpdateOSDescription',
                'workflow.steps.util.host_provider.UpdateHostRootVolumeSize',
            ) + self.get_upgrade_steps_extra() + (
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.database.StartRsyslog',
                'workflow.steps.util.metric_collector.RestartTelegraf',
            ),
        }] + self.get_upgrade_steps_final()

    def get_upgrade_steps_extra(self):
        return (
            'workflow.steps.util.volume_provider.AttachDataVolume',
            'workflow.steps.util.volume_provider.MountDataVolume',
            'workflow.steps.util.plan.InitializationForUpgrade',
            'workflow.steps.util.plan.ConfigureForUpgrade',
            'workflow.steps.util.plan.ConfigureLog',
            'workflow.steps.util.metric_collector.ConfigureTelegraf',
        )

    def get_migrate_engine_steps_extra(self):
        return (
            'workflow.steps.util.volume_provider.AttachDataVolume',
            'workflow.steps.util.volume_provider.MountDataVolume',
            'workflow.steps.util.plan.InitializationForMigrateEngine',
            'workflow.steps.util.plan.ConfigureForMigrateEngine',
            'workflow.steps.util.plan.ConfigureLogMigrateEngine',
            'workflow.steps.util.metric_collector.ConfigureTelegraf',
        )

    def get_upgrade_steps_final(self):
        return [{
            self.get_upgrade_steps_final_description(): (
                'workflow.steps.util.db_monitor.UpdateInfraVersion',
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.DestroyAlarms',
                'workflow.steps.util.zabbix.CreateAlarmsForUpgrade',
            ),
        }]

    def get_migrate_engines_steps(self):
        return [{
            self.get_upgrade_steps_initial_description(): (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
            ),
        }] + [{
            self.get_upgrade_steps_description(): (
                'workflow.steps.util.database.checkAndFixMySQLReplication',
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.CheckIfSwitchMaster',
                'workflow.steps.util.database.StopIfRunning',
                'workflow.steps.util.database.CheckIsDown',
                'workflow.steps.util.database.StopRsyslogIfRunning',
                'workflow.steps.util.host_provider.StopIfRunning',
                'workflow.steps.util.volume_provider.DetachDataVolume',
                'workflow.steps.util.host_provider.InstallMigrateEngineTemplate',
                'workflow.steps.util.host_provider.Start',
                'workflow.steps.util.vm.WaitingBeReady',
                'workflow.steps.util.vm.UpdateOSDescription',
            ) + self.get_migrate_engine_steps_extra() + (
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.host_provider.UpdateHostRootVolumeSize',
                'workflow.steps.util.metric_collector.RestartTelegraf',
            ),
        }] + self.get_migrate_engine_steps_final()

    def get_migrate_engine_steps_final(self):
        return [{
            self.get_upgrade_steps_final_description(): (
                'workflow.steps.util.db_monitor.UpdateInfraVersion',
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.DestroyAlarms',
                'workflow.steps.util.zabbix.CreateAlarmsForMigrateEngine',
            ),
        }]

    def get_change_binaries_upgrade_patch_steps(self):
        return ()

    def get_configure_ssl_libs_and_folder_steps(self):
        return ()

    def get_configure_ssl_ip_steps(self):
        return ()

    def get_configure_ssl_dns_steps(self):
        return ()

    def get_upgrade_patch_steps(self):
        return [{
            'Disable monitoring and alarms': (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
            ),
        }] + [{
            'Upgrading database': (
                'workflow.steps.util.database.checkAndFixMySQLReplication',
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.CheckIfSwitchMaster',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.CheckIsDown',
                ) + self.get_change_binaries_upgrade_patch_steps() + (
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
            ),
        }] + [{
            'Enabling monitoring and alarms': (
                'workflow.steps.util.db_monitor.UpdateInfraVersion',
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
            ),
        }]

    def get_add_database_instances_first_steps(self):
        return (
            'workflow.steps.util.host_provider.AllocateIP',
            'workflow.steps.util.host_provider.CreateVirtualMachine',
            'workflow.steps.util.dns.CreateDNS',
            'workflow.steps.util.dns.CheckIsReady',
            'workflow.steps.util.vm.WaitingBeReady',
            'workflow.steps.util.vm.UpdateOSDescription',
            'workflow.steps.util.volume_provider.NewVolume',
        )

    def get_add_database_instances_last_steps(self):
        return (
            'workflow.steps.util.acl.ReplicateAcls2NewInstance',
            'workflow.steps.util.acl.BindNewInstance',
            'workflow.steps.util.zabbix.CreateAlarms',
            'workflow.steps.util.db_monitor.CreateMonitoring',
            'workflow.steps.util.database.ConfigurePrometheusMonitoring'
        )

    def get_add_database_instances_middle_steps(self):
        return ()

    def get_add_database_instances_steps_description(self):
        return "Add instances"

    def get_remove_readonly_instance_steps_description(self):
        return "Remove instance"

    def get_add_database_instances_steps(self):
        return [{
            self.get_add_database_instances_steps_description():
            self.get_add_database_instances_first_steps() +
            self.get_add_database_instances_middle_steps() +
            self.get_add_database_instances_last_steps()
        }]

    def get_remove_readonly_instance_steps(self):
        return [{
            self.get_remove_readonly_instance_steps_description():
            self.get_add_database_instances_first_steps() +
            self.get_add_database_instances_middle_steps() +
            self.get_add_database_instances_last_steps()
        }]

    def get_change_parameter_steps_description(self):
        return 'Changing database parameters'

    def get_change_parameter_steps_final_description(self):
        return 'Setting parameter status'

    def get_change_parameter_steps_final(self):
        return [{
            self.get_change_parameter_steps_final_description(): (
                'workflow.steps.util.database.SetParameterStatus',
            ),
        }]

    def get_change_parameter_config_steps(self):
        return ('workflow.steps.util.plan.ConfigureOnlyDBConfigFile', )

    def get_change_static_parameter_steps(self):
        return [{
            self.get_change_parameter_steps_description(): (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
                'workflow.steps.util.database.checkAndFixMySQLReplication',
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.CheckIfSwitchMaster',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.CheckIsDown',
            ) + self.get_change_parameter_config_steps() + (
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
            )
        }] + self.get_change_parameter_steps_final()

    def get_change_dinamic_parameter_steps(self):
        return [{
            self.get_change_parameter_steps_description(): self.get_change_parameter_config_steps() +
            (
                'workflow.steps.util.database.ChangeDynamicParameters',
            )
        }] + self.get_change_parameter_steps_final()

    def get_change_dinamic_parameter_retry_steps_count(self):
        return 1

    def get_change_static_parameter_retry_steps_count(self):
        return 2

    def get_resize_oplog_steps(self):
        return ()

    def get_resize_oplog_steps_and_retry_steps_back(self):
        return self.get_resize_oplog_steps(), 0

    def get_database_change_persistence_steps(self):
        return ()

    def get_switch_write_instance_steps_description(self):
        return "Switch write database instance"

    def get_switch_write_instance_steps(self):
        return [{
            self.get_switch_write_instance_steps_description():
            (
                'workflow.steps.util.database.checkAndFixMySQLReplication',
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.CheckIfSwitchMaster',
            )
        }]

    def get_reinstallvm_steps(self):
        return [{
            'Disable monitoring and alarms': (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
            ),
        }] + [{
            'Reinstall VM': (
                'workflow.steps.util.database.checkAndFixMySQLReplicationIfRunning',
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.CheckIfSwitchMaster',
                'workflow.steps.util.database.StopIfRunning',
                'workflow.steps.util.database.StopRsyslogIfRunning',
                'workflow.steps.util.host_provider.StopIfRunning',
                'workflow.steps.util.volume_provider.DetachDataVolume',
                'workflow.steps.util.host_provider.ReinstallTemplate',
                'workflow.steps.util.host_provider.Start',
                'workflow.steps.util.vm.WaitingBeReady',
                'workflow.steps.util.vm.UpdateOSDescription',
                'workflow.steps.util.host_provider.UpdateHostRootVolumeSize',
            ),
        }] + [{
            'Start Database': (
                'workflow.steps.util.volume_provider.AttachDataVolume',
                'workflow.steps.util.volume_provider.MountDataVolume',
                'workflow.steps.util.plan.Initialization',
                'workflow.steps.util.plan.Configure',
                'workflow.steps.util.plan.ConfigureLog',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
                ) + self.get_change_binaries_upgrade_patch_steps() + (
                ) + self.get_reinstallvm_ssl_steps() + (
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.metric_collector.RestartTelegraf',
            ),
        }] + self.get_reinstallvm_steps_final()

    def get_reinstallvm_ssl_steps(self):
        return ()

    def get_reinstallvm_steps_final(self):
        return [{
            'Enabling monitoring and alarms': (
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
                'workflow.steps.util.database.ConfigurePrometheusMonitoring'
            ),
        }]

    def get_configure_ssl_steps(self):
        return [{
            'Disable monitoring and alarms': (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
            ),
        }] + [{
            'Configure SSL': (
                'workflow.steps.util.ssl.UpdateOpenSSlLib',
                'workflow.steps.util.ssl.CreateSSLFolder',
                'workflow.steps.util.ssl.CreateSSLConfForInfraEndPoint',
                'workflow.steps.util.ssl.RequestSSLForInfra',
                'workflow.steps.util.ssl.CreateJsonRequestFileInfra',
                'workflow.steps.util.ssl.CreateCertificateInfra',
                'workflow.steps.util.ssl.SetSSLFilesAccessMySQL',
                'workflow.steps.util.ssl.SetInfraConfiguredSSL',
                'workflow.steps.util.plan.Configure',
                'workflow.steps.util.plan.ConfigureLog',
                'workflow.steps.util.ssl.UpdateExpireAtDate',
            ),
        }] + [{
            'Restart Database': (
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.Start',
            ),
        }] + [{
            'Enabling monitoring and alarms': (
                'workflow.steps.util.db_monitor.UpdateInfraSSLMonitor',
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
            ),
        }]

    def get_host_migrate_steps(self):
        raise NotImplementedError

    def get_database_migrate_steps(self):
        raise NotImplementedError

    def get_database_migrate_steps_stage_1(self):
        return [{
            'Creating Service Account': (
                'workflow.steps.util.host_provider.CreateServiceAccount',
                'workflow.steps.util.host_provider.SetServiceAccountRoles'
            )}, {
            'Creating virtual machine': (
                'workflow.steps.util.host_provider.AllocateIP',
                'workflow.steps.util.host_provider.CreateVirtualMachineMigrate',
                'workflow.steps.util.infra.MigrationCreateInstance',
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
                'workflow.steps.util.plan.Configure',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
            )}, {
            'Backup and restore': (
                'workflow.steps.util.volume_provider.TakeSnapshotMigrate',
                'workflow.steps.util.volume_provider.WaitSnapshotAvailableMigrate',
                'workflow.steps.util.volume_provider.AddHostsAllowMigrateBackupHost',
                'workflow.steps.util.volume_provider.CreatePubKeyMigrateBackupHost',
                'workflow.steps.util.database.StopWithoutUndo',
                'workflow.steps.util.database.CheckIsDown',
                'workflow.steps.util.disk.CleanDataMigrate',
                'workflow.steps.util.volume_provider.NewVolumeMigrateOriginalHost',
                'workflow.steps.util.volume_provider.AttachDataLatestVolumeMigrate',
                'workflow.steps.util.volume_provider.MountDataLatestVolumeMigrate',
                'workflow.steps.util.volume_provider.RsyncFromSnapshotMigrateBackupHost',
                'workflow.steps.util.volume_provider.WaitRsyncFromSnapshotDatabaseMigrate',
                'workflow.steps.util.volume_provider.RemovePubKeyMigrateHostMigrate',
                'workflow.steps.util.volume_provider.RemoveHostsAllowMigrateBackupHost',
                'workflow.steps.util.volume_provider.UmountDataLatestVolumeMigrate',
                'workflow.steps.util.volume_provider.DetachDataLatestVolumeMigrate',
                'workflow.steps.util.volume_provider.DeleteVolumeMigrateOriginalHost',
            )}, {
            'Configure SSL lib and folder': (
                ) + self.get_configure_ssl_libs_and_folder_steps() + (
            )}, {
            'Configure SSL (IP)': (
                ) + self.get_configure_ssl_ip_steps() + (
            )}, {
            'Configure Telegraf': (
                'workflow.steps.util.metric_collector.RestartTelegrafSourceDBMigrateRollback',
                'workflow.steps.util.metric_collector.ConfigureTelegrafSourceDBMigrateRollback',
            )}, {
            'Configure and start database': (
                'workflow.steps.util.disk.RemoveDeprecatedFiles',
                'workflow.steps.util.plan.Configure',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
            )}, {
            'Check access between instances': (
                'workflow.steps.util.vm.CheckAccessToMaster',
                'workflow.steps.util.vm.CheckAccessFromMaster',
            )}, {
            'Replicate ACL': (
                'workflow.steps.util.acl.ReplicateAclsMigrate',
                'workflow.steps.util.acl.BindNewInstanceDatabaseMigrate',
            )}, {
            'Stopping database': (
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.StopRsyslog',
                'workflow.steps.util.database.CheckIsDown',
            )}, {
            'Destroy Alarms': (
                'workflow.steps.util.zabbix.DestroyAlarmsDatabaseMigrate',
            )}, {
            'Update and Check DNS': (
                'workflow.steps.util.infra.UpdateEndpointMigrateRollback',
                'workflow.steps.util.dns.CheckIsReadyDBMigrateRollback',
                'workflow.steps.util.dns.ChangeEndpointDBMigrate',
                'workflow.steps.util.dns.CheckIsReadyDBMigrate',
                'workflow.steps.util.infra.UpdateEndpointMigrate',
            )}, {
            'Configure SSL (DNS)': (
                ) + self.get_configure_ssl_dns_steps() + (
            )}, {
            'Stop source database': (
                'workflow.steps.util.infra.DisableSourceInstances',
                'workflow.steps.util.database.StopSourceDatabaseMigrate',
            )}, {
            'Starting database': (
                'workflow.steps.util.infra.EnableFutureInstances',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.database.StartRsyslog',
                'workflow.steps.util.disk.ChangeSnapshotOwner',
            )}, {
            'Configure Telegraf': (
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
                'workflow.steps.util.metric_collector.RestartTelegraf',
                'workflow.steps.util.metric_collector.ConfigureTelegrafSourceDBMigrate',
                'workflow.steps.util.metric_collector.RestartTelegrafSourceDBMigrate',
            )}, {
            'Recreate Alarms': (
                'workflow.steps.util.zabbix.CreateAlarmsDatabaseMigrate',
                'workflow.steps.util.db_monitor.UpdateInfraCloudDatabaseMigrate',
        )}]


    def get_database_migrate_steps_stage_2(self):
        return [{
            'Cleaning up': (
                'workflow.steps.util.database.StopSourceDatabaseMigrate',
                'workflow.steps.util.database.StopRsyslogMigrate',
                'workflow.steps.util.volume_provider.DestroyOldEnvironment',
                'workflow.steps.util.host_provider.DestroyVirtualMachineMigrate',
                'workflow.steps.util.host_provider.DestroyIPMigrate',
                'workflow.steps.util.host_provider.DestroyServiceAccountMigrate',
        )}]

    def get_database_migrate_steps_stage_3(self):
        raise NotImplementedError

    def get_filer_migrate_steps(self):
        raise NotImplementedError

    def get_restart_database_steps(self):
        return [{
            'Disable monitoring': (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
            )}, {
            'Restarting database': (
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.CheckIfSwitchMaster',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.StopRsyslog',
                'workflow.steps.util.database.CheckIsDown',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.StartRsyslog',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.metric_collector.RestartTelegraf',
            )}, {
            'Enabling monitoring': (
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
            )
        }]

    def get_region_migrate_steps_stage_1(self):
        return [{
            'Creating Service Account': (
                'workflow.steps.util.host_provider.CreateServiceAccount',
                'workflow.steps.util.host_provider.SetServiceAccountRoles'
            )}, {
            'Creating virtual machine': (
                'workflow.steps.util.host_provider.AllocateIPRegionMigrate',
                'workflow.steps.util.host_provider.CreateVirtualMachineRegionMigrate',
                'workflow.steps.util.infra.MigrationCreateInstance',
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
                'workflow.steps.util.plan.Configure',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
            )}, {
            'Backup and restore': (
                'workflow.steps.util.volume_provider.TakeSnapshotMigrate',
                'workflow.steps.util.volume_provider.WaitSnapshotAvailableMigrate',
                'workflow.steps.util.volume_provider.AddHostsAllowMigrateBackupHost',
                'workflow.steps.util.volume_provider.CreatePubKeyMigrateBackupHost',
                'workflow.steps.util.database.StopWithoutUndo',
                'workflow.steps.util.database.CheckIsDown',
                'workflow.steps.util.disk.CleanDataMigrate',
                'workflow.steps.util.volume_provider.NewVolumeMigrateOriginalHost',
                'workflow.steps.util.volume_provider.AttachDataLatestVolumeMigrate',
                'workflow.steps.util.volume_provider.MountDataLatestVolumeMigrate',
                'workflow.steps.util.volume_provider.RsyncFromSnapshotMigrateBackupHost',
                'workflow.steps.util.volume_provider.WaitRsyncFromSnapshotDatabaseMigrate',
                'workflow.steps.util.volume_provider.RemovePubKeyMigrateHostMigrate',
                'workflow.steps.util.volume_provider.RemoveHostsAllowMigrateBackupHost',
                'workflow.steps.util.volume_provider.UmountDataLatestVolumeMigrate',
                'workflow.steps.util.volume_provider.DetachDataLatestVolumeMigrate',
                'workflow.steps.util.volume_provider.DeleteVolumeMigrateOriginalHost',
            )}, {
            'Configure SSL lib and folder': (
                ) + self.get_configure_ssl_libs_and_folder_steps() + (
            )}, {
            'Configure SSL (IP)': (
                ) + self.get_configure_ssl_ip_steps() + (
            )}, {
            'Configure Telegraf': (
                'workflow.steps.util.metric_collector.RestartTelegrafSourceDBMigrateRollback',
                'workflow.steps.util.metric_collector.ConfigureTelegrafSourceDBMigrateRollback',
            )}, {
            'Configure and start database': (
                'workflow.steps.util.disk.RemoveDeprecatedFiles',
                'workflow.steps.util.plan.Configure',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
            )}, {
            'Check access between instances': (
                'workflow.steps.util.vm.CheckAccessToMaster',
                'workflow.steps.util.vm.CheckAccessFromMaster',
            )}, {
            'Replicate ACL': (
                'workflow.steps.util.acl.ReplicateAclsMigrate',
                'workflow.steps.util.acl.BindNewInstanceDatabaseMigrate',
            )}, {
            'Stopping database': (
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.StopRsyslog',
                'workflow.steps.util.database.CheckIsDown',
            )}, {
            'Destroy Alarms': (
                'workflow.steps.util.zabbix.DestroyAlarmsDatabaseMigrate',
            )}, {
            'Update and Check DNS': (
                'workflow.steps.util.infra.UpdateEndpointMigrateRollback',
                'workflow.steps.util.dns.CheckIsReadyDBMigrateRollback',
                'workflow.steps.util.dns.ChangeEndpointDBMigrate',
                'workflow.steps.util.dns.CheckIsReadyDBMigrate',
                'workflow.steps.util.infra.UpdateEndpointMigrate',
            )}, {
            'Configure SSL (DNS)': (
                ) + self.get_configure_ssl_dns_steps() + (
            )}, {
            'Stop source database': (
                'workflow.steps.util.infra.DisableSourceInstances',
                'workflow.steps.util.database.StopSourceDatabaseMigrate',
            )}, {
            'Starting database': (
                'workflow.steps.util.infra.EnableFutureInstances',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.database.StartRsyslog',
                'workflow.steps.util.disk.ChangeSnapshotOwner',
            )}, {
            'Configure Telegraf': (
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
                'workflow.steps.util.metric_collector.RestartTelegraf',
                'workflow.steps.util.metric_collector.ConfigureTelegrafSourceDBMigrate',
                'workflow.steps.util.metric_collector.RestartTelegrafSourceDBMigrate',
            )}, {
            'Recreate Alarms': (
                'workflow.steps.util.zabbix.CreateAlarmsDatabaseMigrate',
                'workflow.steps.util.db_monitor.UpdateInfraCloudDatabaseMigrate',
            )}]

    def get_region_migrate_steps_stage_2(self):
        return [{
            'Cleaning up': (
                'workflow.steps.util.database.StopSourceDatabaseMigrate',
                'workflow.steps.util.database.StopRsyslogMigrate',
                'workflow.steps.util.volume_provider.DestroyOldEnvironment',
                'workflow.steps.util.host_provider.DestroyVirtualMachineMigrate',
                'workflow.steps.util.host_provider.DestroyIPMigrate',
                'workflow.steps.util.host_provider.DestroyServiceAccountMigrate',
            )}]

    def get_region_migrate_steps_stage_3(self):
        raise NotImplementedError

    def get_stop_database_vm_steps(self):
        return [{
            'Disable monitoring and check replication': (
                'workflow.steps.util.zabbix.DisableMonitors',
                'workflow.steps.util.db_monitor.DisableMonitoring',
                'workflow.steps.util.database.checkAndFixMySQLReplication',
            )}, {
            'Stopping database': (
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.StopRsyslog',
                'workflow.steps.util.database.CheckIsDown',
            )}, {
            'Stopping VM': (
                'workflow.steps.util.host_provider.StopIfRunning',
            )
        }]

    def get_start_database_vm_steps(self):
        return [{
            'Starting VM': (
                'workflow.steps.util.host_provider.Start',
                'workflow.steps.util.vm.WaitingBeReady',
            )}, {
            'Starting database': (
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.StartRsyslog',
                'workflow.steps.util.database.CheckIsUp',
            )}, {
            'Restoring master instance': (
                'workflow.steps.util.database.RestoreMasterInstanceFromDatabaseStop',
            )}, {
            'Enable alarms': (
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableMonitors',
            )
        }]


class FakeTestTopology(BaseTopology):

    @property
    def driver_name(self):
        return 'fake'


class InstanceDeploy():

    def __init__(self, instance_type, port):
        self.instance_type = instance_type
        self.port = port
