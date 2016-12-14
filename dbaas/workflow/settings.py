

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


MYSQL_FLIPPER_FOX_MIGRATION_1 = (
    'workflow.steps.mysql.flipperfox_migration.change_ttl.DecreaseTTL',
    'workflow.steps.mysql.flipperfox_migration.create_virtualmachines.CreateVirtualMachine',
    'workflow.steps.mysql.flipperfox_migration.create_vip.CreateVip',
    'workflow.steps.mysql.flipperfox_migration.create_nfs.CreateNfs',
    'workflow.steps.mysql.flipperfox_migration.mount_disks.MountDisks',
    'workflow.steps.mysql.flipperfox_migration.config_files.ConfigFiles',
    'workflow.steps.mysql.flipperfox_migration.uncomment_skip_slave.UncommentSkipSlave',
    'workflow.steps.mysql.flipperfox_migration.make_backup.MakeBackup',
    'workflow.steps.mysql.flipperfox_migration.grant_nfs_access.GrantNFSAccess',
    'workflow.steps.mysql.flipperfox_migration.restore_backup_on_targets.RetoreBackupOnTargets',
    'workflow.steps.mysql.flipperfox_migration.revoke_nfs_access.RevokeNFSAccess',
    'workflow.steps.mysql.flipperfox_migration.remove_nfs_snapshot.RemoveNfsSnapshot',
    'workflow.steps.mysql.flipperfox_migration.start_replication.StartReplication',
    'workflow.steps.mysql.flipperfox_migration.check_pupet.CheckPuppetIsRunning',
    'workflow.steps.mysql.flipperfox_migration.config_vms_foreman.ConfigVMsForeman',
    'workflow.steps.mysql.flipperfox_migration.run_pupet_setup.RunPuppetSetup',
    'workflow.steps.mysql.flipperfox_migration.config_fox.ConfigFox',
    'workflow.steps.mysql.flipperfox_migration.create_foxha_mysql_users.CreateFoxHAMySQLUser',
    'workflow.steps.mysql.flipperfox_migration.config_backup_log.ConfigBackupLog',
    'workflow.steps.mysql.flipperfox_migration.acl_database_bind.BindNewInstances',
    'workflow.steps.mysql.flipperfox_migration.replicate_old_acls.ReplicateOldAcl',
    'workflow.steps.mysql.flipperfox_migration.td_agent.StopTDAgent',
)


MYSQL_FLIPPER_FOX_MIGRATION_2 = (
    'workflow.steps.mysql.flipperfox_migration.check_instances_status.CheckInstancesStatus',
    'workflow.steps.mysql.flipperfox_migration.set_master_read_only.SetMasterReadOnly',
    'workflow.steps.mysql.flipperfox_migration.turn_flipper_ip_down.TurnFlipperIpDown',
    'workflow.steps.mysql.flipperfox_migration.check_replication.CheckReplicationFlipperFox',
    'workflow.steps.mysql.flipperfox_migration.change_master.ChangeMaster',
    'workflow.steps.mysql.flipperfox_migration.check_replication.CheckReplicationFoxFlipper',
    'workflow.steps.mysql.flipperfox_migration.start_fox.StartFox',
    'workflow.steps.mysql.flipperfox_migration.set_infra_endpoint.SetInfraEndpoint',
    'workflow.steps.mysql.flipperfox_migration.update_zabbix_monitoring.UpdateZabbixMonitoring',
    'workflow.steps.mysql.flipperfox_migration.switch_dns.SwitchDNS',
    'workflow.steps.mysql.flipperfox_migration.td_agent.StartTDAgent',
    'workflow.steps.mysql.flipperfox_migration.start_mysql_statsd.StartMySQLStasD',

)

MYSQL_FLIPPER_FOX_MIGRATION_3 = (
    'workflow.steps.mysql.flipperfox_migration.remove_old_acl.RemoveOldAcl',
    'workflow.steps.mysql.flipperfox_migration.acl_database_bind.UnbindOldInstances',
    'workflow.steps.mysql.flipperfox_migration.update_dbaas_metadata.UpdateDBaaSMetadata',
    'workflow.steps.mysql.flipperfox_migration.delete_flipper_dns.DeleteFlipperDNS',
    'workflow.steps.mysql.flipperfox_migration.remove_secondary_ip.RemoveSecondaryIp',
    'workflow.steps.mysql.flipperfox_migration.remove_disks.RemoveDisks',
    'workflow.steps.mysql.flipperfox_migration.remove_vms.RemoveVms',
    'workflow.steps.mysql.flipperfox_migration.change_ttl.DefaultTTL',
)

MYSQL_FLIPPER_FOX_MIGRATION_4 = ()
