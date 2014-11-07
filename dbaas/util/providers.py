from workflow.workflow import stop_workflow, start_workflow
from physical.models import DatabaseInfra
from dbaas_credentials.models import CredentialType
from util import get_credentials_for
import logging
from util import build_dict
import re

LOG = logging.getLogger(__name__)

UNKNOWN = 0
MYSQL = 1
MONGODB = 2

def make_infra(plan, environment, name,task=None):
    if not plan.provider == plan.CLOUDSTACK:
        dbinfra = DatabaseInfra.best_for(plan= plan, environment= environment, name= name)

        if dbinfra:
            return build_dict(databaseinfra= dbinfra, created=True)

        return build_dict(databaseinfra=None, created= False)

    workflow_dict = build_dict(name= name,
                               plan= plan,
                               environment= environment,
                               steps= get_engine_steps(engine= str(plan.engine_type)),
                               qt= get_vm_qt(plan= plan, ),
                               MYSQL = MYSQL,
                               MONGODB = MONGODB,
                               enginecod = get_engine(engine= str(plan.engine_type))
                               )

    start_workflow(workflow_dict= workflow_dict, task=task)
    return workflow_dict



def destroy_infra(databaseinfra, task=None):
    if not databaseinfra.plan.provider == databaseinfra.plan.CLOUDSTACK:
        return True

    instances = []
    hosts = []

    for instance in databaseinfra.instances.all():
        instances.append(instance)
        hosts.append(instance.hostname)

    workflow_dict = build_dict(plan= databaseinfra.plan,
                               environment= databaseinfra.environment,
                               steps= get_engine_steps(engine= str(databaseinfra.plan.engine_type)),
                               qt= get_vm_qt(plan= databaseinfra.plan),
                               hosts= hosts,
                               instances= instances,
                               databaseinfra= databaseinfra,
                               MYSQL = MYSQL,
                               MONGODB = MONGODB,
                               enginecod = get_engine(engine= str(databaseinfra.plan.engine_type))
                               )

    if stop_workflow(workflow_dict= workflow_dict, task=task):
        return workflow_dict
    else:
        return False


def get_engine(engine):
    engine = engine.lower()

    if re.match(r'^mongo.*', engine):
        return MONGODB
    elif re.match(r'^mysql.*', engine):
        return MYSQL
    else:
        return UNKNOWN



def get_engine_steps(engine):

    enginecod = get_engine(engine)

    if enginecod == MONGODB:
        from workflow.settings import DEPLOY_MONGO
        steps = DEPLOY_MONGO
    elif enginecod == MYSQL:
        from workflow.settings import DEPLOY_MYSQL
        steps = DEPLOY_MYSQL
    else:
        from workflow.settings import DEPLOY_UNKNOWN
        steps = DEPLOY_UNKNOWN

    return steps

def get_vm_qt(plan):
    if plan.is_ha:
        if get_engine(engine= str(plan.engine_type)) == MONGODB:
            qt = 3
        else:
            qt = 2
    else:
        qt = 1

    return qt


def get_engine_credentials(engine, environment):
    engine = engine.lower()

    if re.match(r'^mongo.*', engine):
        credential_type = CredentialType.MONGODB
    elif re.match(r'^mysql.*', engine):
        credential_type = CredentialType.MYSQL

    return get_credentials_for(
                environment=environment, credential_type=credential_type)

def resize_database(database, cloudstackpack, task=None):
    
    from dbaas_cloudstack.models import CloudStackPack
    original_cloudstackpack = CloudStackPack.objects.get(offering__serviceofferingid = database.offering_id, 
                                                         offering__region__environment = database.environment, 
                                                         engine_type__name = database.engine_type)
    workflow_dict = build_dict(database= database,
                               cloudstackpack= cloudstackpack,
                               original_cloudstackpack = original_cloudstackpack,
                               environment= database.environment,
                               steps= get_engine_resize_steps(engine= str(database.plan.engine_type)),
                               enginecod = get_engine(engine= str(database.plan.engine_type))
                               )

    start_workflow(workflow_dict= workflow_dict, task=task)
    
    return workflow_dict

def get_engine_resize_steps(engine):

    enginecod = get_engine(engine)

    if enginecod == MONGODB:
        from workflow.settings import RESIZE_MONGO
        steps = RESIZE_MONGO
    elif enginecod == MYSQL:
        from workflow.settings import RESIZE_MYSQL
        steps = RESIZE_MYSQL
    else:
        from workflow.settings import RESIZE_UNKNOWN
        steps = RESIZE_UNKNOWN

    return steps