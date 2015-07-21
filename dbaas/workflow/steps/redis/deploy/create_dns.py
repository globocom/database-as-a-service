# -*- coding: utf-8 -*-
import logging
from util import full_stack
from physical.models import Instance
from dbaas_dnsapi.utils import add_dns_record
from dbaas_dnsapi.provider import DNSAPIProvider
from dbaas_dnsapi.models import HOST
from dbaas_dnsapi.models import INSTANCE
from dbaas_dnsapi.models import DatabaseInfraDNSList
from ...util.base import BaseStep
from ....exceptions.error_codes import DBAAS_0007

LOG = logging.getLogger(__name__)


class CreateDns(BaseStep):

    def __unicode__(self):
        return "Requesting DNS..."

    def do(self, workflow_dict):
        try:
            LOG.info("Creating dns for hosts...")
            for host_name in zip(workflow_dict['hosts'], workflow_dict['names']['vms']):
                host = host_name[0]

                host.hostname = add_dns_record(
                    databaseinfra=workflow_dict['databaseinfra'],
                    name=host_name[1],
                    ip=host.address,
                    type=HOST)
                host.save()

            instances_redis = []
            instances_sentinel = []

            for instance in workflow_dict['instances']:
                if instance.instance_type == Instance.REDIS_SENTINEL:
                    instances_sentinel.append(instance)
                else:
                    instances_redis.append(instance)

            LOG.info("Creating dns for instances...")
            for instance_name in zip(instances_redis, workflow_dict['names']['vms']):
                instance = instance_name[0]

                instance.dns = add_dns_record(
                    databaseinfra=workflow_dict['databaseinfra'],
                    name=instance_name[1],
                    ip=instance.address,
                    type=INSTANCE)
                instance.save()

                if workflow_dict['qt'] == 1:
                    LOG.info("Updating databaseinfra dns endpoint")
                    databaseinfra = workflow_dict['databaseinfra']
                    databaseinfra.endpoint_dns = instance.dns + \
                        ':%i' % instance.port
                    databaseinfra.save()
                    workflow_dict['databaseinfra'] = databaseinfra

            LOG.info("Creating dns for sentinel instances...")
            for instance_name in zip(instances_sentinel, workflow_dict['names']['vms']):
                instance = instance_name[0]

                instance.dns = add_dns_record(
                    databaseinfra=workflow_dict['databaseinfra'],
                    name=instance_name[1],
                    ip=instance.address,
                    type=INSTANCE,
                    database_sufix='sentinel')
                instance.save()

            LOG.info("Calling dnsapi provider...")
            DNSAPIProvider.create_database_dns(
                databaseinfra=workflow_dict['databaseinfra'])

            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0007)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        try:
            DNSAPIProvider.remove_database_dns(
                environment=workflow_dict['environment'],
                databaseinfraid=workflow_dict['databaseinfra'].id)

            DatabaseInfraDNSList.objects.filter(
                databaseinfra=workflow_dict['databaseinfra'].id).delete()

            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0007)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
