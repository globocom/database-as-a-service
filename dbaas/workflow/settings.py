
DEPLOY_MYSQL = (
            'workflow.steps.build_databaseinfra.BuildDatabaseInfra',
            'workflow.steps.create_virtualmachines.CreateVirtualMachine',
            'workflow.steps.create_secondary_ip.CreateSecondaryIp',
            'workflow.steps.create_dns.CreateDns',
            'workflow.steps.create_nfs.CreateNfs',
            'workflow.steps.create_flipper.CreateFlipper',
            'workflow.steps.init_database.InitDatabase',
            'workflow.steps.build_database.BuildDatabase',
            'workflow.steps.check_dns.CheckDns',
            'workflow.steps.create_zabbix.CreateZabbix',
            'workflow.steps.create_dbmonitor.CreateDbMonitor'
    )

