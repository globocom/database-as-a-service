import logging
import re
from util import build_dict
from util import slugify
from util import get_credentials_for
from util import get_replication_topology_instance
from dbaas_credentials.models import CredentialType
from physical.models import DatabaseInfra
from logical.models import Database
from workflow.workflow import stop_workflow
from workflow.workflow import start_workflow, start_workflow_ha

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
        steps=get_deploy_settings(
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


def get_cloudstack_pack(database):
    from dbaas_cloudstack.models import CloudStackPack

    return CloudStackPack.objects.get(
        offering__serviceofferingid=database.offering_id,
        offering__region__environment=database.environment,
        engine_type__name=database.engine_type
    )


def get_not_resized_instances_of(database, cloudstackpack):
    from dbaas_cloudstack.provider import CloudStackProvider
    from physical.models import Instance

    cs_credentials = get_credentials_for(
        environment=database.environment,
        credential_type=CredentialType.CLOUDSTACK
    )
    cs_provider = CloudStackProvider(credentials=cs_credentials)
    all_instances = database.infra.instances.all()
    engine_name = database.infra.engine.engine_type.name
    not_resized_instances = []

    if engine_name == "redis":
        instances_to_test = all_instances.filter(instance_type=Instance.REDIS)
    elif engine_name == "mongodb":
        instances_to_test = all_instances.filter(instance_type=Instance.MONGODB)
    else:
        instances_to_test = all_instances

    for instance in instances_to_test:
        host = instance.hostname
        host_attr = host.cs_host_attributes.get()

        offering_id = cs_provider.get_vm_offering_id(
            vm_id=host_attr.vm_id,
            project_id=cs_credentials.project
        )

        if offering_id == cloudstackpack.offering.serviceofferingid:
            LOG.info("Instance {} of database {} offering: {}".format(
                instance.hostname, database.name, offering_id
            ))
        else:
            not_resized_instances.append(instance)

    return not_resized_instances


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


def get_clone_settings(class_path):
    return get_replication_topology_instance(class_path).get_clone_steps()


def get_resize_settings(class_path):
    return get_replication_topology_instance(class_path).get_resize_steps()


def get_restore_snapshot_settings(class_path):
    return get_replication_topology_instance(class_path).get_restore_snapshot_steps()


def get_database_upgrade_setting(class_path):
    return get_replication_topology_instance(class_path).get_upgrade_steps()


def get_engine_credentials(engine, environment):
    engine = engine.lower()

    if re.match(r'^mongo.*', engine):
        credential_type = CredentialType.MONGODB
    elif re.match(r'^mysql.*', engine):
        credential_type = CredentialType.MYSQL
    elif re.match(r'^redis.*', engine):
        credential_type = CredentialType.MYSQL

    return get_credentials_for(
        environment=environment,
        credential_type=credential_type
    )
