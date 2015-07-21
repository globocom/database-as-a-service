# -*- coding: utf-8 -*-
import logging
from util import full_stack
from dbaas_dnsapi.utils import add_dns_record
from dbaas_dnsapi.provider import DNSAPIProvider
from dbaas_dnsapi.models import HOST
from dbaas_dnsapi.models import FLIPPER
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

            if 'databaseinfraattr' in workflow_dict:

                LOG.info("Creating dns for databaseinfraattr...")
                for infra_attr in workflow_dict['databaseinfraattr']:

                    if infra_attr.is_write:
                        dnsname = workflow_dict['databaseinfra'].name
                    else:
                        dnsname = workflow_dict['databaseinfra'].name + '-r'

                    dnsname = add_dns_record(
                        databaseinfra=workflow_dict['databaseinfra'],
                        name=dnsname,
                        ip=infra_attr.ip,
                        type=FLIPPER)

                    infra_attr.dns = dnsname
                    infra_attr.save()

                    if infra_attr.is_write:
                        LOG.info("Updating databaseinfra dns endpoint")
                        databaseinfra = workflow_dict['databaseinfra']
                        databaseinfra.endpoint_dns = infra_attr.dns + \
                            ':%i' % 3306
                        databaseinfra.save()
                        workflow_dict['databaseinfra'] = databaseinfra

            LOG.info("Creating dns for hosts...")
            for host_name in zip(workflow_dict['hosts'], workflow_dict['names']['vms']):
                host = host_name[0]

                host.hostname = add_dns_record(
                    databaseinfra=workflow_dict['databaseinfra'],
                    name=host_name[
                        1],
                    ip=host.address,
                    type=HOST)
                host.save()

            LOG.info("Creating dns for instances...")
            for instance_name in zip(workflow_dict['instances'], workflow_dict['names']['vms']):
                instance = instance_name[0]

                instance.dns = add_dns_record(
                    databaseinfra=workflow_dict['databaseinfra'],
                    name=instance_name[
                        1],
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
