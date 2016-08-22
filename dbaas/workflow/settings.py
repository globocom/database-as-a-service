

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
    'workflow.steps.util.region_migration.td_agent.StopTDAgent',
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
    'workflow.steps.mysql.region_migration.start_mkheartbeat.StartMkHeartbeat',
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
    'workflow.steps.util.region_migration.td_agent.StopTDAgent',
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
    'workflow.steps.util.region_migration.td_agent.StopTDAgent',
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

MYSQL_FLIPPER_FOX_MIGRATION_1 = (
    #'workflow.steps.util.region_migration.change_ttl.DecreaseTTL',
    'workflow.steps.mysql.flipperfox_migration.create_virtualmachines.CreateVirtualMachine',
    'workflow.steps.mysql.flipperfox_migration.create_nfs.CreateNfs',
    'workflow.steps.mysql.flipperfox_migration.mount_disks.MountDisks',
    #'workflow.steps.mysql.flipperfox_migration.create_secondary_ip.CreateSecondaryIp',
    #'workflow.steps.mysql.flipperfox_migration.config_files.ConfigFiles',
    #'workflow.steps.mysql.flipperfox_migration.make_backup.MakeBackup',
    #'workflow.steps.mysql.flipperfox_migration.grant_nfs_access.GrantNFSAccess',
    #'workflow.steps.mysql.flipperfox_migration.restore_backup_on_targets.RetoreBackupOnTargets',
    #'workflow.steps.mysql.flipperfox_migration.revoke_nfs_access.RevokeNFSAccess',
    #'workflow.steps.mysql.flipperfox_migration.remove_nfs_snapshot.RemoveNfsSnapshot',
    #'workflow.steps.mysql.flipperfox_migration.start_replication.StartReplication',
    #'workflow.steps.util.region_migration.config_backup_log.ConfigBackupLog',
    #'workflow.steps.util.region_migration.acl_database_bind.BindNewInstances',
    #'workflow.steps.util.region_migration.replicate_old_acls.ReplicateOldAcl',
    #'workflow.steps.util.region_migration.td_agent.StopTDAgent',
)


MYSQL_FLIPPER_FOX_MIGRATION_2 = (
    'workflow.steps.util.region_migration.check_instances_status.CheckInstancesStatus',
    'workflow.steps.mysql.flipperfox_migration.set_master_read_only.SetMasterReadOnly',
    'workflow.steps.mysql.flipperfox_migration.turn_flipper_ip_down.TurnFlipperIpDown',
    'workflow.steps.mysql.flipperfox_migration.check_replication.CheckReplication',
    'workflow.steps.mysql.flipperfox_migration.change_master.ChangeMaster',
    'workflow.steps.mysql.flipperfox_migration.rename_flipper_masterpair.RenameFlipperMasterPair',
    'workflow.steps.mysql.flipperfox_migration.create_flipper.CreateFlipper',
    'workflow.steps.mysql.flipperfox_migration.set_flipper_ips.SetFlipperIps',
    'workflow.steps.util.region_migration.update_zabbix_host.UpdateZabbixHost',
    'workflow.steps.util.region_migration.switch_dns.SwitchDNS',
    'workflow.steps.util.region_migration.td_agent.StartTDAgent',
    'workflow.steps.mysql.flipperfox_migration.start_mysql_statsd.StartMySQLStasD',
    'workflow.steps.mysql.flipperfox_migration.start_mkheartbeat.StartMkHeartbeat',
)

MYSQL_FLIPPER_FOX_MIGRATION_3 = (
    'workflow.steps.util.region_migration.remove_old_acl.RemoveOldAcl',
    'workflow.steps.util.region_migration.update_dbaas_metadata.UpdateDBaaSMetadata',
    'workflow.steps.util.region_migration.acl_database_bind.UnbindOldInstances',
    'workflow.steps.mysql.flipperfox_migration.remove_secondary_ip.RemoveSecondaryIp',
    'workflow.steps.util.region_migration.remove_disks.RemoveDisks',
    'workflow.steps.util.region_migration.remove_backup_log.RemoveBackupLog',
    'workflow.steps.util.region_migration.remove_vms.RemoveVms',
    'workflow.steps.util.region_migration.change_ttl.DefaultTTL',
)

MYSQL_FLIPPER_FOX_MIGRATION_4 = ()
