DEPLOY_MYSQL_WORKFLOW = (
	'util.gen_names',
	'util.gen_dbinfra',
	'dbaas_cloudstack.create_vm'
	)

DEPLOY_VIRTUALMACHINE = (
            'workflow.steps.build_databaseinfra.BuildDatabaseInfra',
            'workflow.steps.create_virtualmachines.CreateVirtualMachine',


    )

DEPLOY_MONGO_WORKFLOW = (
	'util.gen_names',
	'util.gen_dbinfra',
	'dbaas_cloudstack.create_vm'
	)

