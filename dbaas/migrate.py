from dbaas_cloudstack.models import OfferingGroup as CloudStackOfferingGroup, CloudStackBundle, PlanAttr, CloudStackPack, CloudStackOffering
from physical.models import Offering
import re
from util import get_credentials_for
from dbaas_credentials.models import CredentialType
from pprint import pprint
from pymongo import MongoClient


PROVIDER = 'cloudstack'

def migrate_off(old_off, plan, strong=True):
    if old_off:
        params = dict(
            cpus=old_off.cpus,
            memory_size_mb=old_off.memory_size_mb,
        )

        off = Offering.objects.get(**params)

        if strong:
            plan.stronger_offering = off
        else:
            plan.weaker_offering = off
        plan.save()

for cs_off in CloudStackOffering.objects.all():

    env = cs_off.region.environment
    cpus = cs_off.cpus
    memory_size_mb = cs_off.memory_size_mb
    environment = cs_off.region.environment
    off_key = '{}c{}m'.format(cpus, memory_size_mb)
    params = dict(
        cpus=cpus, memory_size_mb=memory_size_mb,
    )

    try:
        off = Offering.objects.get(**params)
    except Offering.DoesNotExist:
        params.update({
            'name': cs_off.name.replace(" (weaker)", "")
        })
        off = Offering.objects.create(**params)

    if not off.environments.filter(id=environment.id).exists():
        off.environments.add(environment)

for plan_attr in PlanAttr.objects.all():
    plan = plan_attr.plan
    migrate_off(plan_attr.get_stronger_offering(), plan)
    migrate_off(plan_attr.get_weaker_offering(), plan, strong=False)
