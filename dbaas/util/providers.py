import logging
from util import build_dict
from util import slugify
from util import get_credentials_for
from util import get_replication_topology_instance
from dbaas_credentials.models import CredentialType
from physical.models import DatabaseInfra
from logical.models import Database
from workflow.workflow import stop_workflow
from workflow.workflow import start_workflow

LOG = logging.getLogger(__name__)


def make_infra(
    plan, environment, name, team, project, description,
    subscribe_to_email_events=True, task=None, is_protected=False
):
    if not plan.provider == plan.CLOUDSTACK:
        dbinfra = DatabaseInfra.best_for(
            plan=plan, environment=environment, name=name
        )

        if dbinfra:
            database = Database.provision(databaseinfra=dbinfra, name=name)
            database.team = team
            database.description = description
            database.project = project
            database.subscribe_to_email_events = subscribe_to_email_events
            database.save()

            return build_dict(
                databaseinfra=dbinfra, database=database, created=True
            )
        return build_dict(databaseinfra=None, created=False)

    workflow_dict = build_dict(
        name=slugify(name), plan=plan, environment=environment,
        steps=get_deploy_settings(
            plan.replication_topology.class_path
        ), qt=get_vm_qt(plan=plan, ), dbtype=str(plan.engine_type),
        team=team, project=project, description=description,
        subscribe_to_email_events=subscribe_to_email_events,
        is_protected=is_protected
    )

    start_workflow(workflow_dict=workflow_dict, task=task)
    return workflow_dict


def clone_infra(
        plan, environment, name, team, project, description,
        subscribe_to_email_events, task=None, clone=None
):
    if not plan.provider == plan.CLOUDSTACK:
        infra = DatabaseInfra.best_for(
            plan=plan, environment=environment, name=name)

        if infra:
            database = Database.provision(databaseinfra=infra, name=name)
            database.team = team
            database.description = description
            database.project = project
            database.save()

            return build_dict(
                databaseinfra=infra, database=database, created=True,
                subscribe_to_email_events=subscribe_to_email_events
            )

        return build_dict(
            databaseinfra=None, created=False,
            subscribe_to_email_events=subscribe_to_email_events
        )

    workflow_dict = build_dict(
        name=slugify(name),
        plan=plan,
        environment=environment,
        steps=get_clone_settings(
            plan.replication_topology.class_path
        ),
        qt=get_vm_qt(plan=plan),
        dbtype=str(plan.engine_type),
        team=team,
        project=project,
        description=description,
        clone=clone,
        subscribe_to_email_events=subscribe_to_email_events,
    )

    start_workflow(workflow_dict=workflow_dict, task=task)
    return workflow_dict


def destroy_infra(databaseinfra, task=None):

    try:
        database = databaseinfra.databases.get()
        LOG.debug('Database found! {}'.format(database))
    except IndexError:
        LOG.info("Database not found...")

    if not databaseinfra.plan.provider == databaseinfra.plan.CLOUDSTACK:
        LOG.error('Databaseinfra is not cloudstack infra')
        return True

    instances = []
    hosts = []

    for instance in databaseinfra.instances.all():
        instances.append(instance)
        hosts.append(instance.hostname)

    workflow_dict = build_dict(
        plan=databaseinfra.plan,
        environment=databaseinfra.environment,
        steps=get_destroy_settings(
            databaseinfra.plan.replication_topology.class_path
        ),
        qt=get_vm_qt(plan=databaseinfra.plan),
        dbtype=str(databaseinfra.plan.engine_type),
        hosts=hosts,
        instances=instances,
        databaseinfra=databaseinfra,
        database=database
    )

    if stop_workflow(workflow_dict=workflow_dict, task=task):
        return workflow_dict
    else:
        return False


def get_vm_qt(plan):
    if plan.is_ha:
        if plan.engine_type.name == 'mongodb':
            qt = 3
        elif plan.engine_type.name == 'redis':
            qt = 3
        else:
            qt = 2
    else:
        qt = 1

    return qt


def get_deploy_settings(class_path):
    return get_replication_topology_instance(class_path).get_deploy_steps()


def get_destroy_settings(class_path):
    return get_replication_topology_instance(class_path).get_destroy_steps()


def get_deploy_instances(class_path):
    return get_replication_topology_instance(class_path).deploy_instances()


def get_clone_settings(class_path):
    return get_replication_topology_instance(class_path).get_clone_steps()


def get_resize_settings(class_path):
    return get_replication_topology_instance(class_path).get_resize_steps()


def get_restore_snapshot_settings(class_path):
    return get_replication_topology_instance(class_path).get_restore_snapshot_steps()


def get_database_upgrade_setting(class_path):
    return get_replication_topology_instance(class_path).get_upgrade_steps()


def get_reinstallvm_steps_setting(class_path):
    return get_replication_topology_instance(class_path).get_reinstallvm_steps()


def get_database_configure_ssl_setting(class_path):
    return get_replication_topology_instance(class_path).get_configure_ssl_steps()


def get_database_change_parameter_setting(class_path, all_dinamic, custom_procedure):
    replication_topology = get_replication_topology_instance(class_path)
    if custom_procedure:
        custom_proc_method = getattr(replication_topology, custom_procedure)
        return custom_proc_method()[0]
    elif all_dinamic:
        return replication_topology.get_change_dinamic_parameter_steps()
    else:
        return replication_topology.get_change_static_parameter_steps()


def get_database_change_parameter_retry_steps_count(class_path, all_dinamic, custom_procedure):
    replication_topology = get_replication_topology_instance(class_path)

    if custom_procedure:
        custom_proc_method = getattr(replication_topology, custom_procedure)
        return custom_proc_method()[1]
    elif all_dinamic:
        return replication_topology.get_change_dinamic_parameter_retry_steps_count()
    else:
        return replication_topology.get_change_static_parameter_retry_steps_count()


def get_add_database_instances_steps(class_path):
    return get_replication_topology_instance(class_path).get_add_database_instances_steps()


def get_remove_readonly_instance_steps(class_path):
    return get_replication_topology_instance(class_path).get_remove_readonly_instance_steps()


def get_switch_write_instance_steps(class_path):
    return get_replication_topology_instance(class_path).get_switch_write_instance_steps()


def get_host_migrate_steps(class_path):
    return get_replication_topology_instance(class_path).get_host_migrate_steps()


def get_engine_credentials(engine, environment):
    engine = engine.lower()

    if engine.startswith('mongo'):
        credential_type = CredentialType.MONGODB
    elif engine.startswith(('mysql', 'redis')):
        credential_type = CredentialType.MYSQL

    return get_credentials_for(
        environment=environment,
        credential_type=credential_type
    )
