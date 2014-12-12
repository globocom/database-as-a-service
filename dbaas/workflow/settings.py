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
)

DEPLOY_REDIS = (
    'workflow.steps.redis.deploy.build_databaseinfra.BuildDatabaseInfra',
    'workflow.steps.redis.deploy.create_virtualmachines.CreateVirtualMachine',
    'workflow.steps.util.deploy.create_dns.CreateDns',
    'workflow.steps.util.deploy.create_nfs.CreateNfs',
    'workflow.steps.redis.deploy.init_database.InitDatabaseRedis',
    'workflow.steps.util.deploy.check_database_connection.CheckDatabaseConnection',
    'workflow.steps.util.deploy.check_dns.CheckDns',
    'workflow.steps.util.deploy.create_zabbix.CreateZabbix',
    'workflow.steps.util.deploy.create_dbmonitor.CreateDbMonitor',
    'workflow.steps.util.deploy.build_database.BuildDatabase',
    'workflow.steps.util.deploy.create_log.CreateLog',
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
    ('workflow.steps.mongodb.resize.start_database.StartDatabase',)
)

RESIZE_MYSQL = (
    ('workflow.steps.mysql.resize.init_variables.InitVariables',
    'workflow.steps.mysql.resize.stop_database.StopDatabase',
    'workflow.steps.mysql.resize.change_config.ChangeDatabaseConfigFile',)
    + STOP_RESIZE_START +
    ('workflow.steps.resize.mysql.start_database.StartDatabase',)
)

RESIZE_REDIS = (
    ('workflow.steps.redis.resize.init_variables.InitVariables',
    'workflow.steps.redis.resize.stop_database.StopDatabase',
    'workflow.steps.redis.resize.change_config.ChangeDatabaseConfigFile',)
    + STOP_RESIZE_START +
    ('workflow.steps.resize.redis.start_database.StartDatabase',)

)

RESIZE_UNKNOWN = (

)

