DEPLOY_MYSQL = (
    'workflow.steps.util.deploy.build_databaseinfra.BuildDatabaseInfra',
    'workflow.steps.mysql.deploy.create_virtualmachines.CreateVirtualMachine',
    'workflow.steps.mysql.deploy.create_secondary_ip.CreateSecondaryIp',
    'workflow.steps.mysql.deploy.create_dns.CreateDns',
    'workflow.steps.util.deploy.create_nfs.CreateNfs',
    'workflow.steps.mysql.deploy.create_flipper.CreateFlipper',
    'workflow.steps.mysql.deploy.init_database.InitDatabase',
    'workflow.steps.util.deploy.config_backup_log.ConfigBackupLog',
    'workflow.steps.util.deploy.check_database_connection.CheckDatabaseConnection',
    'workflow.steps.util.deploy.check_dns.CheckDns',
    'workflow.steps.util.deploy.create_zabbix.CreateZabbix',
    'workflow.steps.util.deploy.start_monit.StartMonit',
    'workflow.steps.util.deploy.create_dbmonitor.CreateDbMonitor',
    'workflow.steps.util.deploy.build_database.BuildDatabase',
    'workflow.steps.util.deploy.create_log.CreateLog',
    'workflow.steps.util.deploy.check_database_binds.CheckDatabaseBinds',
)

DEPLOY_MONGO = (
    'workflow.steps.util.deploy.build_databaseinfra.BuildDatabaseInfra',
    'workflow.steps.mongodb.deploy.create_virtualmachines.CreateVirtualMachine',
    'workflow.steps.util.deploy.create_dns.CreateDns',
    'workflow.steps.mongodb.deploy.create_nfs.CreateNfs',
    'workflow.steps.mongodb.deploy.init_database.InitDatabaseMongoDB',
    'workflow.steps.util.deploy.config_backup_log.ConfigBackupLog',
    'workflow.steps.util.deploy.check_database_connection.CheckDatabaseConnection',
    'workflow.steps.util.deploy.check_dns.CheckDns',
    'workflow.steps.util.deploy.create_zabbix.CreateZabbix',
    'workflow.steps.util.deploy.start_monit.StartMonit',
    'workflow.steps.util.deploy.create_dbmonitor.CreateDbMonitor',
    'workflow.steps.util.deploy.build_database.BuildDatabase',
    'workflow.steps.util.deploy.create_log.CreateLog',
    'workflow.steps.util.deploy.check_database_binds.CheckDatabaseBinds',
)

DEPLOY_REDIS = (
    'workflow.steps.redis.deploy.build_databaseinfra.BuildDatabaseInfra',
    'workflow.steps.redis.deploy.create_virtualmachines.CreateVirtualMachine',
    'workflow.steps.redis.deploy.create_dns.CreateDns',
    'workflow.steps.redis.deploy.create_nfs.CreateNfs',
    'workflow.steps.redis.deploy.init_database.InitDatabaseRedis',
    'workflow.steps.util.deploy.config_backup_log.ConfigBackupLog',
    'workflow.steps.util.deploy.check_database_connection.CheckDatabaseConnection',
    'workflow.steps.util.deploy.check_dns.CheckDns',
    'workflow.steps.util.deploy.create_zabbix.CreateZabbix',
    'workflow.steps.util.deploy.start_monit.StartMonit',
    'workflow.steps.util.deploy.create_dbmonitor.CreateDbMonitor',
    'workflow.steps.util.deploy.build_database.BuildDatabase',
    'workflow.steps.util.deploy.create_log.CreateLog',
    'workflow.steps.util.deploy.check_database_binds.CheckDatabaseBinds',
)

DEPLOY_UNKNOWN = (

)

STOP_RESIZE_START = (
    'workflow.steps.util.resize.stop_vm.StopVM',
    'workflow.steps.util.resize.resize_vm.ResizeVM',
    'workflow.steps.util.resize.start_vm.StartVM',
)

RESIZE_MONGO = (
    ('workflow.steps.util.volume_migration.stop_database.StopDatabase',) +
    STOP_RESIZE_START +
    ('workflow.steps.util.resize.start_database.StartDatabase',
     'workflow.steps.util.resize.start_agents.StartAgents',
     'workflow.steps.util.resize.check_database_status.CheckDatabaseStatus',)
)

RESIZE_MYSQL = (
    ('workflow.steps.util.volume_migration.stop_database.StopDatabase',
     'workflow.steps.mysql.resize.change_config.ChangeDatabaseConfigFile',) +
    STOP_RESIZE_START +
    ('workflow.steps.util.resize.start_database.StartDatabase',
     'workflow.steps.util.resize.start_agents.StartAgents',
     'workflow.steps.util.resize.check_database_status.CheckDatabaseStatus',)
)

RESIZE_REDIS = (
    ('workflow.steps.util.volume_migration.stop_database.StopDatabase',
     'workflow.steps.redis.resize.change_config.ChangeDatabaseConfigFile',) +
    STOP_RESIZE_START +
    ('workflow.steps.util.resize.start_database.StartDatabase',
     'workflow.steps.util.resize.start_agents.StartAgents',
     'workflow.steps.util.resize.check_database_status.CheckDatabaseStatus',)

)

RESIZE_UNKNOWN = (

)

CLONE_MONGO = (
    DEPLOY_MONGO +
    ('workflow.steps.util.clone.clone_database.CloneDatabase',
     'workflow.steps.util.resize.check_database_status.CheckDatabaseStatus',)
)

CLONE_MYSQL = (
    DEPLOY_MYSQL +
    ('workflow.steps.util.clone.clone_database.CloneDatabase',
     'workflow.steps.util.resize.check_database_status.CheckDatabaseStatus',)
)

CLONE_REDIS = (
    DEPLOY_REDIS +
    ('workflow.steps.redis.clone.clone_database.CloneDatabase',
     'workflow.steps.util.resize.check_database_status.CheckDatabaseStatus',)
)

CLONE_UNKNOWN = (

)


MYSQL_REGION_MIGRATION_1 = (
    'workflow.steps.util.region_migration.change_ttl.DecreaseTTL',
    'workflow.steps.mysql.region_migration.create_virtualmachines.CreateVirtualMachine',
    'workflow.steps.util.region_migration.create_nfs.CreateNfs',
    'workflow.steps.util.region_migration.mount_disks.MountDisks',
    'workflow.steps.mysql.region_migration.create_secondary_ip.CreateSecondaryIp',
    'workflow.steps.mysql.region_migration.config_files.ConfigFiles',
    'workflow.steps.mysql.region_migration.make_backup.MakeBackup',
    'workflow.steps.mysql.region_migration.grant_nfs_access.GrantNFSAccess',
    'workflow.steps.mysql.region_migration.restore_backup_on_targets.RetoreBackupOnTargets',
    'workflow.steps.mysql.region_migration.revoke_nfs_access.RevokeNFSAccess',
    'workflow.steps.mysql.region_migration.remove_nfs_snapshot.RemoveNfsSnapshot',
    'workflow.steps.mysql.region_migration.start_replication.StartReplication',
    'workflow.steps.util.region_migration.config_backup_log.ConfigBackupLog',
    'workflow.steps.util.region_migration.acl_database_bind.BindNewInstances',
    'workflow.steps.util.region_migration.replicate_old_acls.ReplicateOldAcl',
)


MYSQL_REGION_MIGRATION_2 = (
    'workflow.steps.util.region_migration.check_instances_status.CheckInstancesStatus',
    'workflow.steps.mysql.region_migration.set_master_read_only.SetMasterReadOnly',
    'workflow.steps.mysql.region_migration.turn_flipper_ip_down.TurnFlipperIpDown',
    'workflow.steps.mysql.region_migration.check_replication.CheckReplication',
    'workflow.steps.mysql.region_migration.change_master.ChangeMaster',
    'workflow.steps.mysql.region_migration.rename_flipper_masterpair.RenameFlipperMasterPair',
    'workflow.steps.mysql.region_migration.create_flipper.CreateFlipper',
    'workflow.steps.mysql.region_migration.set_flipper_ips.SetFlipperIps',
    'workflow.steps.util.region_migration.update_zabbix_host.UpdateZabbixHost',
    'workflow.steps.util.region_migration.switch_dns.SwitchDNS',
    'workflow.steps.util.region_migration.td_agent.StartTDAgent',
    'workflow.steps.mysql.region_migration.start_mysql_statsd.StartMySQLStasD',
)

MYSQL_REGION_MIGRATION_3 = (
    'workflow.steps.util.region_migration.remove_old_acl.RemoveOldAcl',
    'workflow.steps.util.region_migration.update_dbaas_metadata.UpdateDBaaSMetadata',
    'workflow.steps.util.region_migration.acl_database_bind.UnbindOldInstances',
    'workflow.steps.mysql.region_migration.remove_secondary_ip.RemoveSecondaryIp',
    'workflow.steps.util.region_migration.remove_disks.RemoveDisks',
    'workflow.steps.util.region_migration.remove_backup_log.RemoveBackupLog',
    'workflow.steps.util.region_migration.remove_vms.RemoveVms',
    'workflow.steps.util.region_migration.change_ttl.DefaultTTL',
)

MYSQL_REGION_MIGRATION_4 = ()

REDIS_REGION_MIGRATION_1 = (
    'workflow.steps.util.region_migration.change_ttl.DecreaseTTL',
    'workflow.steps.redis.region_migration.create_virtualmachines.CreateVirtualMachine',
    'workflow.steps.util.region_migration.create_nfs.CreateNfs',
    'workflow.steps.util.region_migration.mount_disks.MountDisks',
    'workflow.steps.redis.region_migration.config_files.ConfigFiles',
    'workflow.steps.redis.region_migration.start_database_and_replication.StartDatabaseReplication',
    'workflow.steps.util.region_migration.config_backup_log.ConfigBackupLog',
    'workflow.steps.util.region_migration.acl_database_bind.BindNewInstances',
    'workflow.steps.util.region_migration.replicate_old_acls.ReplicateOldAcl',
)
REDIS_REGION_MIGRATION_2 = (
    'workflow.steps.util.region_migration.check_instances_status.CheckInstancesStatus',
    'workflow.steps.util.region_migration.check_replication.CheckReplication',
    'workflow.steps.redis.region_migration.switch_master.SwitchMaster',
)
REDIS_REGION_MIGRATION_3 = (
    'workflow.steps.util.region_migration.update_zabbix_host.UpdateZabbixHost',
    'workflow.steps.util.region_migration.switch_dns.SwitchDNS',
    'workflow.steps.util.region_migration.td_agent.StartTDAgent',
)
REDIS_REGION_MIGRATION_4 = (
    'workflow.steps.util.region_migration.remove_old_acl.RemoveOldAcl',
    'workflow.steps.util.region_migration.acl_database_bind.UnbindOldInstances',
    'workflow.steps.redis.region_migration.remove_old_instances.RemoveInstances',
    'workflow.steps.util.region_migration.update_dbaas_metadata.UpdateDBaaSMetadata',
    'workflow.steps.util.region_migration.remove_disks.RemoveDisks',
    'workflow.steps.util.region_migration.remove_backup_log.RemoveBackupLog',
    'workflow.steps.util.region_migration.remove_vms.RemoveVms',
    'workflow.steps.util.region_migration.change_ttl.DefaultTTL',
)
REDIS_REGION_MIGRATION_5 = ()

MONGODB_REGION_MIGRATION_1 = (
    'workflow.steps.util.region_migration.change_ttl.DecreaseTTL',
    'workflow.steps.mongodb.region_migration.create_virtualmachines.CreateVirtualMachine',
    'workflow.steps.util.region_migration.create_nfs.CreateNfs',
    'workflow.steps.util.region_migration.mount_disks.MountDisks',
    'workflow.steps.mongodb.region_migration.config_files.ConfigFiles',
    'workflow.steps.mongodb.region_migration.add_instances_replica_set.AddInstancesReplicaSet',
    'workflow.steps.util.region_migration.config_backup_log.ConfigBackupLog',
    'workflow.steps.util.region_migration.acl_database_bind.BindNewInstances',
    'workflow.steps.util.region_migration.replicate_old_acls.ReplicateOldAcl',
)
MONGODB_REGION_MIGRATION_2 = (
    'workflow.steps.util.region_migration.check_instances_status.CheckInstancesStatus',
    'workflow.steps.util.region_migration.check_replication.CheckReplication',
    'workflow.steps.mongodb.region_migration.switch_primary.SwitchPrimary',
)
MONGODB_REGION_MIGRATION_3 = (
    'workflow.steps.util.region_migration.update_zabbix_host.UpdateZabbixHost',
    'workflow.steps.util.region_migration.switch_dns.SwitchDNS',
    'workflow.steps.util.region_migration.td_agent.StartTDAgent',
)
MONGODB_REGION_MIGRATION_4 = (
    'workflow.steps.util.region_migration.remove_old_acl.RemoveOldAcl',
    'workflow.steps.util.region_migration.update_dbaas_metadata.UpdateDBaaSMetadata',
    'workflow.steps.util.region_migration.acl_database_bind.UnbindOldInstances',
    'workflow.steps.mongodb.region_migration.remove_old_instances_replica_set.RemoveInstancesReplicaSet',
    'workflow.steps.util.region_migration.remove_disks.RemoveDisks',
    'workflow.steps.util.region_migration.remove_backup_log.RemoveBackupLog',
    'workflow.steps.util.region_migration.remove_vms.RemoveVms',
    'workflow.steps.util.region_migration.change_ttl.DefaultTTL',
)
MONGODB_REGION_MIGRATION_5 = ()


RESTORE_SNAPSHOT_SINGLE = (
    'workflow.steps.util.restore_snapshot.restore_snapshot.RestoreSnapshot',
    'workflow.steps.util.restore_snapshot.grant_nfs_access.GrantNFSAccess',
    'workflow.steps.util.restore_snapshot.stop_database.StopDatabase',
    'workflow.steps.util.restore_snapshot.umount_data_volume.UmountDataVolume',
    'workflow.steps.util.restore_snapshot.update_fstab.UpdateFstab',
    'workflow.steps.util.restore_snapshot.mount_data_volume.MountDataVolume',
    'workflow.steps.util.restore_snapshot.start_database.StartDatabase',
    'workflow.steps.util.restore_snapshot.make_export_snapshot.MakeExportSnapshot',
    'workflow.steps.util.restore_snapshot.update_dbaas_metadata.UpdateDbaaSMetadata',
    'workflow.steps.util.restore_snapshot.clean_old_volumes.CleanOldVolumes',
)


RESTORE_SNAPSHOT_MYSQL_HA = (
    'workflow.steps.mysql.restore_snapshot.restore_snapshot.RestoreSnapshot',
    'workflow.steps.util.restore_snapshot.grant_nfs_access.GrantNFSAccess',
    'workflow.steps.mysql.restore_snapshot.stop_database.StopDatabase',
    'workflow.steps.mysql.restore_snapshot.umount_data_volume.UmountDataVolume',
    'workflow.steps.util.restore_snapshot.update_fstab.UpdateFstab',
    'workflow.steps.util.restore_snapshot.mount_data_volume.MountDataVolume',
    'workflow.steps.mysql.restore_snapshot.start_database_and_replication.StartDatabaseAndReplication',
    'workflow.steps.util.restore_snapshot.make_export_snapshot.MakeExportSnapshot',
    'workflow.steps.util.restore_snapshot.update_dbaas_metadata.UpdateDbaaSMetadata',
    'workflow.steps.util.restore_snapshot.clean_old_volumes.CleanOldVolumes',
)


VOLUME_MIGRATION = (
    'workflow.steps.util.volume_migration.create_volume.CreateVolume',
    'workflow.steps.util.volume_migration.mount_volume.MountVolume',
    'workflow.steps.util.volume_migration.stop_database.StopDatabase',
    'workflow.steps.util.volume_migration.copy_data.CopyData',
    'workflow.steps.util.volume_migration.umount_volumes.UmountVolumes',
    'workflow.steps.util.volume_migration.update_fstab.UpdateFstab',
    'workflow.steps.util.volume_migration.start_database.StartDatabase',
    'workflow.steps.util.volume_migration.update_dbaas_metadata.UpdateDbaaSMetadata',
)

MONGODB_UPGRADE_24_TO_30_SINGLE = (
    'workflow.steps.mongodb.upgrade.upgrade_mongodb_24_to_26_single.UpgradeMongoDB_24_to_26',
    'workflow.steps.mongodb.upgrade.upgrade_mongodb_26_to_30_single.UpgradeMongoDB_26_to_30',
    'workflow.steps.mongodb.upgrade.prereq_change_storage_engine_single.PreReqChangeMongoDBStorageEngine',
    'workflow.steps.mongodb.upgrade.take_instance_snapshot.TakeInstanceBackup',
    'workflow.steps.mongodb.upgrade.change_storage_engine_single.ChangeMongoDBStorageEngine',
    'workflow.steps.mongodb.upgrade.update_plan.UpdatePlan',
    'workflow.steps.mongodb.upgrade.update_engine.UpdateEngine',
    'workflow.steps.mongodb.upgrade.update_dbmonitor_version.UpdateDBMonitorDatabasInfraVersion',
)

MONGODB_UPGRADE_24_TO_30_HA = (
    'workflow.steps.mongodb.upgrade.upgrade_mongodb_24_to_26_ha.UpgradeMongoDB_24_to_26',
    'workflow.steps.mongodb.upgrade.upgrade_mongodb_26_to_30_ha.UpgradeMongoDB_26_to_30',
    'workflow.steps.mongodb.upgrade.take_instance_snapshot.TakeInstanceBackup',
    'workflow.steps.mongodb.upgrade.change_storage_engine_ha.ChangeMongoDBStorageEngine',
    'workflow.steps.mongodb.upgrade.update_plan.UpdatePlan',
    'workflow.steps.mongodb.upgrade.update_engine.UpdateEngine',
    'workflow.steps.mongodb.upgrade.update_dbmonitor_version.UpdateDBMonitorDatabasInfraVersion',
)
