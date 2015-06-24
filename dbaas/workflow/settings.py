DEPLOY_MYSQL = (
    'workflow.steps.util.deploy.build_databaseinfra.BuildDatabaseInfra',
    'workflow.steps.mysql.deploy.create_virtualmachines.CreateVirtualMachine',
    'workflow.steps.mysql.deploy.create_secondary_ip.CreateSecondaryIp',
    'workflow.steps.mysql.deploy.create_dns.CreateDns',
    'workflow.steps.util.deploy.create_nfs.CreateNfs',
    'workflow.steps.mysql.deploy.create_flipper.CreateFlipper',
    'workflow.steps.mysql.deploy.init_database.InitDatabase',
    'workflow.steps.util.deploy.check_database_connection.CheckDatabaseConnection',
    'workflow.steps.util.deploy.check_dns.CheckDns',
    'workflow.steps.util.deploy.create_zabbix.CreateZabbix',
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
    'workflow.steps.util.deploy.check_database_connection.CheckDatabaseConnection',
    'workflow.steps.util.deploy.check_dns.CheckDns',
    'workflow.steps.util.deploy.create_zabbix.CreateZabbix',
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
    'workflow.steps.util.deploy.check_database_connection.CheckDatabaseConnection',
    'workflow.steps.util.deploy.check_dns.CheckDns',
    'workflow.steps.util.deploy.create_zabbix.CreateZabbix',
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
    ('workflow.steps.mongodb.resize.init_variables.InitVariables',
     'workflow.steps.mongodb.resize.stop_database.StopDatabase',)
     + STOP_RESIZE_START +
    ('workflow.steps.mongodb.resize.start_database.StartDatabase',
     'workflow.steps.util.resize.check_database_status.CheckDatabaseStatus',)
)

RESIZE_MYSQL = (
    ('workflow.steps.mysql.resize.init_variables.InitVariables',
     'workflow.steps.mysql.resize.stop_database.StopDatabase',
     'workflow.steps.mysql.resize.change_config.ChangeDatabaseConfigFile',)
     + STOP_RESIZE_START +
    ('workflow.steps.mysql.resize.start_database.StartDatabase',
     'workflow.steps.util.resize.check_database_status.CheckDatabaseStatus',)
)

RESIZE_REDIS = (
    ('workflow.steps.redis.resize.init_variables.InitVariables',
     'workflow.steps.redis.resize.stop_database.StopDatabase',
     'workflow.steps.redis.resize.change_config.ChangeDatabaseConfigFile',)
     + STOP_RESIZE_START +
    ('workflow.steps.redis.resize.start_database.StartDatabase',
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
    'workflow.steps.util.region_migration.create_virtualmachines.CreateVirtualMachine',
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
)


MYSQL_REGION_MIGRATION_2 = (
    'workflow.steps.mysql.region_migration.set_master_read_only.SetMasterReadOnly',
    'workflow.steps.mysql.region_migration.turn_flipper_ip_down.TurnFlipperIpDown',
    'workflow.steps.mysql.region_migration.check_replication.CheckReplication',
    'workflow.steps.mysql.region_migration.change_master.ChangeMaster',
    'workflow.steps.mysql.region_migration.rename_flipper_masterpair.RenameFlipperMasterPair',
    'workflow.steps.mysql.region_migration.create_flipper.CreateFlipper',
    'workflow.steps.mysql.region_migration.set_flipper_ips.SetFlipperIps',
    'workflow.steps.util.region_migration.switch_dns.SwitchDNS',
)

MYSQL_REGION_MIGRATION_3 = (
    'workflow.steps.util.region_migration.td_agent.StartTDAgent',
    'workflow.steps.mysql.region_migration.start_mysql_statsd.StartMySQLStasD',
    'workflow.steps.util.region_migration.update_dbaas_metadata.UpdateDBaaSMetadata',
    'workflow.steps.mysql.region_migration.remove_secondary_ip.RemoveSecondaryIp',
    'workflow.steps.util.region_migration.remove_disks.RemoveDisks',
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
)
REDIS_REGION_MIGRATION_2 = (
    'workflow.steps.util.region_migration.check_replication.CheckReplication',
    'workflow.steps.redis.region_migration.switch_master.SwitchMaster',
)
REDIS_REGION_MIGRATION_3 = (
    'workflow.steps.util.region_migration.switch_dns.SwitchDNS',
)
REDIS_REGION_MIGRATION_4 = (
    'workflow.steps.redis.region_migration.remove_old_instances.RemoveInstances',
    'workflow.steps.util.region_migration.update_dbaas_metadata.UpdateDBaaSMetadata',
    'workflow.steps.util.region_migration.td_agent.StartTDAgent',
    'workflow.steps.util.region_migration.remove_disks.RemoveDisks',
    'workflow.steps.util.region_migration.remove_vms.RemoveVms',
    'workflow.steps.util.region_migration.change_ttl.DefaultTTL',
)
REDIS_REGION_MIGRATION_5 = ()

MONGODB_REGION_MIGRATION_1 = (
    'workflow.steps.util.region_migration.change_ttl.DecreaseTTL',
    'workflow.steps.util.region_migration.create_virtualmachines.CreateVirtualMachine',
    'workflow.steps.util.region_migration.create_nfs.CreateNfs',
    'workflow.steps.util.region_migration.mount_disks.MountDisks',
    'workflow.steps.mongodb.region_migration.config_files.ConfigFiles',
    'workflow.steps.mongodb.region_migration.add_instances_replica_set.AddInstancesReplicaSet',
)
MONGODB_REGION_MIGRATION_2 = (
    'workflow.steps.util.region_migration.check_replication.CheckReplication',
    'workflow.steps.mongodb.region_migration.switch_primary.SwitchPrimary',
)
MONGODB_REGION_MIGRATION_3 = (
    'workflow.steps.util.region_migration.switch_dns.SwitchDNS',
)
MONGODB_REGION_MIGRATION_4 = (
    'workflow.steps.util.region_migration.update_dbaas_metadata.UpdateDBaaSMetadata',
    'workflow.steps.util.region_migration.td_agent.StartTDAgent',
    'workflow.steps.mongodb.region_migration.remove_old_instances_replica_set.RemoveInstancesReplicaSet',
    'workflow.steps.util.region_migration.remove_disks.RemoveDisks',
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
