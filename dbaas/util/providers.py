import logging
import re
from util import build_dict
from util import slugify
from util import get_credentials_for
from dbaas_credentials.models import CredentialType
from physical.models import DatabaseInfra
from logical.models import Database
from workflow.workflow import stop_workflow
from workflow.workflow import start_workflow
from drivers.factory import DriverFactory

LOG = logging.getLogger(__name__)


def make_infra(plan, environment, name, team, project, description, task=None,):
    if not plan.provider == plan.CLOUDSTACK:
        dbinfra = DatabaseInfra.best_for(plan=plan, environment=environment,
                                         name=name)

        if dbinfra:
            database = Database.provision(databaseinfra=dbinfra, name=name)
            database.team = team
            database.description = description
            database.project = project
            database.save()

            return build_dict(databaseinfra=dbinfra, database=database,
                              created=True)

        return build_dict(databaseinfra=None, created=False)

    workflow_dict = build_dict(name=slugify(name),
                               plan=plan,
                               environment=environment,
                               steps=get_deploy_settings(
                                   plan.engine_type.name),
                               qt=get_vm_qt(plan=plan, ),
                               dbtype=str(plan.engine_type),
                               team=team,
                               project=project,
                               description=description,
                               )

    start_workflow(workflow_dict=workflow_dict, task=task)
    return workflow_dict


def clone_infra(plan, environment, name, team, project, description, task=None, clone=None):
    if not plan.provider == plan.CLOUDSTACK:
        dbinfra = DatabaseInfra.best_for(
            plan=plan, environment=environment, name=name)

        if dbinfra:
            database = Database.provision(databaseinfra=dbinfra, name=name)
            database.team = team
            database.description = description
            database.project = project
            database.save()

            return build_dict(databaseinfra=dbinfra, database=database, created=True)

        return build_dict(databaseinfra=None, created=False)

    workflow_dict = build_dict(name=slugify(name),
                               plan=plan,
                               environment=environment,
                               steps=get_clone_settings(plan.engine_type.name),
                               qt=get_vm_qt(plan=plan, ),
                               dbtype=str(plan.engine_type),
                               team=team,
                               project=project,
                               description=description,
                               clone=clone
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

    workflow_dict = build_dict(plan=databaseinfra.plan,
                               environment=databaseinfra.environment,
                               steps=get_deploy_settings(
                                   databaseinfra.plan.engine_type.name),
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
    original_cloudstackpack = CloudStackPack.objects.get(offering__serviceofferingid=database.offering_id,
                                                         offering__region__environment=database.environment,
                                                         engine_type__name=database.engine_type)

    workflow_dict = build_dict(database=database,
                               databaseinfra=database.databaseinfra,
                               cloudstackpack=cloudstackpack,
                               original_cloudstackpack=original_cloudstackpack,
                               environment=database.environment,
                               instance=instance,
                               host=instance.hostname,
                               steps=get_resize_settings(database.engine_type),
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


def get_deploy_settings(engine_type):
    db_driver_class = DriverFactory.get_driver_class(driver_name=engine_type)
    return db_driver_class.DEPLOY


def get_clone_settings(engine_type):
    db_driver_class = DriverFactory.get_driver_class(driver_name=engine_type)
    return db_driver_class.CLONE


def get_resize_settings(engine_type):
    db_driver_class = DriverFactory.get_driver_class(driver_name=engine_type)
    return db_driver_class.RESIZE


def get_engine_credentials(engine, environment):
    engine = engine.lower()

    if re.match(r'^mongo.*', engine):
        credential_type = CredentialType.MONGODB
    elif re.match(r'^mysql.*', engine):
        credential_type = CredentialType.MYSQL
    elif re.match(r'^redis.*', engine):
        credential_type = CredentialType.MYSQL

    return get_credentials_for(
        environment=environment, credential_type=credential_type)
