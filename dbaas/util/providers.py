from workflow.workflow import stop_workflow, start_workflow
from physical.models import DatabaseInfra
import logging
from util import build_dict

LOG = logging.getLogger(__name__)


def make_infra(plan, environment, name, steps=None,task=None):
    if not plan.provider == plan.CLOUDSTACK:
        dbinfra = DatabaseInfra.best_for(plan= plan, environment= environment, name= name)

        if dbinfra:
            return {'databaseinfra':dbinfra}

        return False

    if not steps:
        return False

    if plan.is_ha:
        qt = 2
    else:
        qt= 1

    workflow_dict = build_dict(name= name, plan= plan, environment= environment, steps= steps, qt= qt)

    if start_workflow(workflow_dict= workflow_dict, task=task):
        return workflow_dict
    else:
        return False


def destroy_infra(databaseinfra, steps=None,task=None):
    if not databaseinfra.plan.provider == databaseinfra.plan.CLOUDSTACK:
        return True

    if not steps:
        return False

    if databaseinfra.plan.is_ha:
        qt = 2
    else:
        qt= 1

    instances = []
    hosts = []

    for instance in databaseinfra.instances.all():
        instances.append(instance)
        hosts.append(instance.hostname)

    workflow_dict = build_dict(plan= databaseinfra.plan, environment= databaseinfra.environment,
        steps= steps, qt= qt, hosts= hosts, instances= instances, databaseinfra= databaseinfra)


    if stop_workflow(workflow_dict= workflow_dict, task=task):
        return workflow_dict
    else:
        return False
