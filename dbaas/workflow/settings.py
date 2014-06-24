DEPLOY_MYSQL_WORKFLOW = (
	'util.gen_names',
	'util.gen_dbinfra',
	'dbaas_cloudstack.create_vm'
	)

DEPLOY_VIRTUALMACHINE = (
            'workflow.steps.build_databaseinfra.BuildDatabaseInfra',
            'workflow.steps.create_virtualmachines.CreateVirtualMachine',
            'workflow.steps.create_dns.CreateDns',
            'workflow.steps.create_nfs.CreateNfs',


    )

DEPLOY_MONGO_WORKFLOW = (
	'util.gen_names',
	'util.gen_dbinfra',
	'dbaas_cloudstack.create_vm'
	)

