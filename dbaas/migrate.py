from dbaas_cloudstack.models import OfferingGroup as CloudStackOfferingGroup, CloudStackBundle, PlanAttr
from physical.models import Offering
import re
from util import get_credentials_for
from dbaas_credentials.models import CredentialType
from pprint import pprint
from pymongo import MongoClient


PROVIDER = 'cloudstack'
offerings = {}
mongo_hp = MongoClient('mongodb://localhost:27017/host_provider')
mongo_table = mongo_hp.host_provider

def migrate_off(old_off, plan, strong=True):
    if old_off:
        params = dict(
            cpus=old_off.cpus,
            memory_size_mb=old_off.memory_size_mb,
            environment=old_off.region.environment,
            name=old_off.name.replace("(weaker)", "")
        )

        off, created = Offering.objects.get_or_create(**params)
        if strong:
            plan.stronger_offering = off
        else:
            plan.weaker_offering = off
        plan.save()

for plan_attr in PlanAttr.objects.all():
    plan = plan_attr.plan
    migrate_off(plan_attr.get_stronger_offering(), plan)
    migrate_off(plan_attr.get_weaker_offering(), plan, strong=False)

for cs_group in CloudStackOfferingGroup.objects.all():

    for cs_off in cs_group.offerings.all():

        env = cs_off.region.environment
        cpus = cs_off.cpus
        memory_size_mb = cs_off.memory_size_mb
        environment = cs_off.region.environment
        off_key = '{}c{}m'.format(cpus, memory_size_mb)
        params = dict(
            cpus=cpus, memory_size_mb=memory_size_mb,
            environment=environment,
            name=cs_off.name
        )

        off, created = Offering.objects.get_or_create(**params)

        offerings.setdefault(env, {}).update({
            off_key: {
                'name': cs_off.name,
                'id': cs_off.serviceofferingid
            }
        })


zones = {}
templates = {}
for cs_bundle in CloudStackBundle.objects.all():
    parsed_name = re.search(r'.*(.*)', cs_bundle.name)
    parsed_name = re.search(r'.*(CMA\w\d\d\w\w).*', cs_bundle.name)
    zone_name = (parsed_name and parsed_name.groups()[0]) or cs_bundle.name
    env = cs_bundle.region.environment
    zones.setdefault(env, {}).setdefault(cs_bundle.zoneid, {
        'id': cs_bundle.zoneid,
        'name': zone_name,
        'active': cs_bundle.is_active,
        'networks': {}
    })

    if parsed_name:
        zones[env][cs_bundle.zoneid]['name'] = parsed_name.groups()[0]
    network_key = cs_bundle.engine.full_name_for_host_provider
    net_letter_number = 65 + len(zones[env][cs_bundle.zoneid]['networks'].get(network_key, []))
    net = zones[env][cs_bundle.zoneid]['networks'].setdefault(
        network_key, []
    )
    if cs_bundle.networkid not in map(lambda n: n['networkId'], net or []):
        net.append({
            'networkId': cs_bundle.networkid,
            'name': '{} - {}'.format(zone_name, chr(net_letter_number))
        })

    templates.setdefault(env, {})[network_key] = cs_bundle.templateid


mongo_data = {}
for env in Environment.objects.all():
    credential = get_credentials_for(env, CredentialType.CLOUDSTACK)
    mongo_data = {
        'environment': env.name,
        'provider': 'cloudstack',
        'projectid': credential.project,
        'api_key': credential.token,
        'secret_key': credential.secret,
        'endpoint': credential.endpoint,
        'zones': zones[env],
        'templates': templates[env],
        'offerings': offerings[env]
    }
    mongo_table.credential.find_one_and_update(
        {"provider": "cloudstack", "environment": env.name},
        {"$set": mongo_data}, upsert=True
    )
