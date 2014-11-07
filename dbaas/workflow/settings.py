
DEPLOY_MYSQL = (
            'workflow.steps.build_databaseinfra.BuildDatabaseInfra',
            'workflow.steps.create_virtualmachines.CreateVirtualMachine',
            'workflow.steps.create_secondary_ip.CreateSecondaryIp',
            'workflow.steps.create_dns.CreateDns',
            'workflow.steps.create_nfs.CreateNfs',
            'workflow.steps.create_flipper.CreateFlipper',
            'workflow.steps.init_database.InitDatabase',
            'workflow.steps.check_database_connection.CheckDatabaseConnection',
            'workflow.steps.check_dns.CheckDns',
            'workflow.steps.create_zabbix.CreateZabbix',
            'workflow.steps.create_dbmonitor.CreateDbMonitor'
)


DEPLOY_MONGO = (
            'workflow.steps.build_databaseinfra.BuildDatabaseInfra',
            'workflow.steps.create_virtualmachines.CreateVirtualMachine',
            'workflow.steps.create_dns.CreateDns',
            'workflow.steps.create_nfs.CreateNfs',
            'workflow.steps.init_database_mongodb.InitDatabaseMongoDB',
            'workflow.steps.check_database_connection.CheckDatabaseConnection',
            'workflow.steps.check_dns.CheckDns',
            'workflow.steps.create_zabbix.CreateZabbix',
            'workflow.steps.create_dbmonitor.CreateDbMonitor'
)

DEPLOY_UNKNOWN = (

)

RESIZE_MONGO = (
    'workflow.steps.resize.mongodb.init_variables.InitVariables',
    'workflow.steps.resize.mongodb.stop_database.StopDatabase',
    'workflow.steps.resize.mongodb.stop_vm.StopVM',
    'workflow.steps.resize.mongodb.resize_vm.ResizeVM',
    'workflow.steps.resize.mongodb.start_vm.StartVM',
    'workflow.steps.resize.mongodb.start_database.StartDatabase',
)

RESIZE_MYSQL = (
    'workflow.steps.resize.mysql.init_variables.InitVariables',
    'workflow.steps.resize.mysql.stop_database.StopDatabase',
    'workflow.steps.resize.mysql.change_config.ChangeDatabaseConfigFile',
    'workflow.steps.resize.mysql.stop_vm.StopVM',
    'workflow.steps.resize.mysql.resize_vm.ResizeVM',
    'workflow.steps.resize.mysql.start_vm.StartVM',
    'workflow.steps.resize.mysql.start_database.StartDatabase',
)

RESIZE_UNKNOWN = (

)