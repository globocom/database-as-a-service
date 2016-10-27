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
from workflow.workflow import start_workflow

LOG = logging.getLogger(__name__)


def make_infra(
    plan, environment, name, team, project, description, contacts,
    subscribe_to_email_events=True, task=None,
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
            database.contacts = contacts
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
        contacts=contacts,
    )

    start_workflow(workflow_dict=workflow_dict, task=task)
    return workflow_dict


def clone_infra(
        plan, environment, name, team, project, description,
        subscribe_to_email_events, contacts, task=None, clone=None
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
                contacts=contacts,
                subscribe_to_email_events=subscribe_to_email_events
            )

        return build_dict(
            databaseinfra=None, created=False, contacts=contacts,
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
        contacts=contacts
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


def resize_database_instance(database, cloudstackpack, instance, task=None):

    from dbaas_cloudstack.models import CloudStackPack

    original_cloudstackpack = CloudStackPack.objects.get(
        offering__serviceofferingid=database.offering_id,
        offering__region__environment=database.environment,
        engine_type__name=database.engine_type
    )

    workflow_dict = build_dict(
        database=database,
        databaseinfra=database.databaseinfra,
        cloudstackpack=cloudstackpack,
        original_cloudstackpack=original_cloudstackpack,
        environment=database.environment,
        instance=instance,
        host=instance.hostname,
        steps=get_resize_settings(
            database.databaseinfra.plan.replication_topology.class_path
        )
    )

    start_workflow(workflow_dict=workflow_dict, task=task)
    return workflow_dict


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
