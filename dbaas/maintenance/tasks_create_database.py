from datetime import datetime
from notification.models import TaskHistory
from physical.models import DatabaseInfra, Instance
from util import slugify, gen_infra_names, make_db_random_password
from workflow.workflow import steps_for_instances
from models import DatabaseCreate


def get_or_create_infra(base_name, plan, environment, retry_from=None):
    if retry_from:
        infra = retry_from.infra
        base_name['infra'] = infra.name
        base_name['name_prefix'] = infra.name_prefix
        base_name['name_stamp'] = infra.name_stamp
    else:
        infra = DatabaseInfra()
        infra.name = base_name['infra']
        infra.name_prefix = base_name['name_prefix']
        infra.name_stamp = base_name['name_stamp']
        infra.last_vm_created = 0
        infra.password = make_db_random_password()
        infra.engine = plan.engine
        infra.plan = plan
        infra.disk_offering = plan.disk_offering
        infra.environment = environment
        infra.capacity = 1
        infra.per_database_size_mbytes = plan.max_db_size
        infra.save()

    return infra


def create_database(
    name, plan, environment, team, project, description,
    subscribe_to_email_events=True, is_protected=False, user=None,
    retry_from=None
):
    # ToDo plan.replication_topology.initial_size
    number_of_vms = 6
    name = slugify(name)
    base_name = gen_infra_names(name, number_of_vms)

    infra = get_or_create_infra(base_name, plan, environment, retry_from)

    task = TaskHistory()
    task.task_id = datetime.now().strftime("%Y%m%d%H%M%S")
    task.task_name = "create_database"
    task.task_status = TaskHistory.STATUS_RUNNING
    task.context = {'infra': infra}
    task.arguments = {'infra': infra}
    task.user = 'admin'
    task.save()

    instances = []
    for i in range(number_of_vms):
        try:
            instance = infra.instances.get(
                hostname__hostname__startswith='{}-0{}-{}'.format(
                    base_name['name_prefix'], i+1, base_name['name_stamp']
                )
            )
        except Instance.DoesNotExist:
            instance = Instance()
            instance.dns = base_name['vms'][i]
            instance.vm_name = instance.dns
            instance.databaseinfra = infra
            # ToDo ALL engines
            instance.port = 6379
            instance.instance_type = Instance.REDIS

        instances.append(instance)

    database_create = DatabaseCreate()
    database_create.task = task
    database_create.name = name
    database_create.plan = plan
    database_create.environment = environment
    database_create.team = team
    database_create.project = project
    database_create.description = description
    database_create.subscribe_to_email_events = subscribe_to_email_events
    database_create.is_protected = is_protected
    database_create.user = 'admin'
    database_create.infra = infra
    database_create.database = infra.databases.first()
    database_create.save()

    steps = [{
        'Creating virtual machine': (
            'workflow.steps.util.vm.CreateVirtualMachineNewInfra',
        )}, {
        'Creating dns': (
            'workflow.steps.util.dns.CreateDNS',
        )}, {
        'Creating disk': (
            'workflow.steps.util.disk.CreateExport',
        )}, {
        'Waiting VMs': (
            'workflow.steps.util.vm.WaitingBeReady',
            'workflow.steps.util.vm.UpdateOSDescription'
        )}, {
        'Configuring database': (
            'workflow.steps.util.plan.InitializationForNewInfra',
            'workflow.steps.util.plan.ConfigureForNewInfra',
            'workflow.steps.util.database.Start',
            'workflow.steps.util.database.CheckIsUp',
        )}, {
        'Configuring Cluster': (
            # ToDo Generic
            'workflow.steps.redis.cluster.CreateCluster',
            'workflow.steps.redis.cluster.CheckClusterStatus',
        )}, {
        'Check DNS': (
            'workflow.steps.util.dns.CheckIsReady',
        )}, {
        'Creating Database': (
            'workflow.steps.util.database.Create',
        )}, {
        'Creating monitoring and alarms': (
            'workflow.steps.util.zabbix.CreateAlarms',
        )
    }]

    since_step = None
    if retry_from:
        since_step = retry_from.current_step

    if steps_for_instances(
        steps, instances, task, database_create.update_step,
        since_step=since_step
    ):
        task.set_status_success('Database created')
    else:
        task.set_status_error('Could not create database')

