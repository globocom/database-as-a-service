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


MYSQL_REGION_MIGRATION = ()
REDIS_REGION_MIGRATION = ()

MONGODB_REGION_MIGRATION_1 = (
    'workflow.steps.mongodb.region_migration.change_ttl.DecreaseTTL',
    'workflow.steps.mongodb.region_migration.create_virtualmachines.CreateVirtualMachine',
    'workflow.steps.mongodb.region_migration.create_nfs.CreateNfs',
    'workflow.steps.mongodb.region_migration.mount_disks.MountDisks',
    'workflow.steps.mongodb.region_migration.config_files.ConfigFiles',
    'workflow.steps.mongodb.region_migration.add_instances_replica_set.AddInstancesReplicaSet',
)
MONGODB_REGION_MIGRATION_2 = (
    'workflow.steps.mongodb.region_migration.switch_primary.SwitchPrimary',
)
MONGODB_REGION_MIGRATION_3 = (
    'workflow.steps.mongodb.region_migration.switch_dns.SwitchDNS',
)
MONGODB_REGION_MIGRATION_4 = (
    'workflow.steps.mongodb.region_migration.update_dbaas_metadata.UpdateDBaaSMetadata',
    'workflow.steps.mongodb.region_migration.remove_old_instances_replica_set.RemoveInstancesReplicaSet',
    'workflow.steps.mongodb.region_migration.remove_disks.RemoveDisks',
    'workflow.steps.mongodb.region_migration.remove_vms.RemoveVms',
    'workflow.steps.mongodb.region_migration.change_ttl.DefaultTTL',
)
MONGODB_REGION_MIGRATION_5 = ()
