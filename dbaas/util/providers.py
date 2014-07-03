from workflow.workflow import stop_workflow, start_workflow
from physical.models import DatabaseInfra
from dbaas_credentials.models import CredentialType
from util import get_credentials_for
import logging
from util import build_dict
import re

LOG = logging.getLogger(__name__)


def make_infra(plan, environment, name,task=None):
    if not plan.provider == plan.CLOUDSTACK:
        dbinfra = DatabaseInfra.best_for(plan= plan, environment= environment, name= name)

        if dbinfra:
            return {'databaseinfra':dbinfra}

        return False

    workflow_dict = build_dict(name= name, plan= plan, environment= environment,
                                            steps= get_engine_steps(engine= str(plan.engine_type)),
                                            qt= get_vm_qt(plan= plan))

    if start_workflow(workflow_dict= workflow_dict, task=task):
        return workflow_dict
    else:
        return False


def destroy_infra(databaseinfra, task=None):
    if not databaseinfra.plan.provider == databaseinfra.plan.CLOUDSTACK:
        return True

    instances = []
    hosts = []

    for instance in databaseinfra.instances.all():
        instances.append(instance)
        hosts.append(instance.hostname)

    workflow_dict = build_dict(plan= databaseinfra.plan, environment= databaseinfra.environment,
                                            steps= get_engine_steps(engine= str(databaseinfra.plan.engine_type)),
                                            qt= get_vm_qt(plan= databaseinfra.plan),
                                            hosts= hosts, instances= instances, databaseinfra= databaseinfra)

    if stop_workflow(workflow_dict= workflow_dict, task=task):
        return workflow_dict
    else:
        return False



def get_engine_steps(engine):
    engine = engine.lower()

    if re.match(r'^mongo.*', engine):
        from workflow.settings import DEPLOY_MONGO
        steps = DEPLOY_MONGO
    elif re.match(r'^mysql.*', engine):
        from workflow.settings import DEPLOY_MYSQL
        steps = DEPLOY_MYSQL

    return steps

def get_vm_qt(plan):
    if plan.is_ha:
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

