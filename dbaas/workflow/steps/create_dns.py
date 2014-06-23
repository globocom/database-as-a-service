# -*- coding: utf-8 -*-
import logging
from base import BaseStep
from dbaas_dnsapi.util import add_dns_record
from dbaas_dnsapi.provider import DNSAPIProvider
from dbaas_dnsapi.models import HOST, FLIPPER, INSTANCE
#from util import get_credentials_for

LOG = logging.getLogger(__name__)

class CreateDns(BaseStep):

    def do(self, workflow_dict):

        for infra_attr in workflow_dict['databaseinfraattr']:

            if infra_attr.is_write:
                dnsname = workflow_dict['databaseinfra'].name
            else:
                dnsname = workflow_dict['databaseinfra'].name + '-r'

            dnsname = add_dns_record(databaseinfra= workflow_dict['databaseinfra'],
                                                     name= dnsname,
                                                     ip= infra_attr.ip,
                                                     type= FLIPPER)


        for host_name in zip(workflow_dict['hosts'], workflow_dict['names']['vms']):
            host = host_name[0]

            host.hostname = add_dns_record(databaseinfra= workflow_dict['databaseinfra'],
                                                             name= host_name[1],
                                                             ip= host.addres,
                                                             type= HOST)
            host.save()

        for instance_name in zip(workflow_dict['instances'], workflow_dict['names']['vms']):
            instance = instance_name[0]

            instance.dns = add_dns_record(databaseinfra= workflow_dict['databaseinfra'],
                                                          name= instance_name[1],
                                                          ip= instance.addres,
                                                          type= INSTANCE)
            instance.save()


        DNSAPIProvider.create_database_dns(databaseinfra=workflow_dict['databaseinfra'])



    def undo(self, workflow_dict):
        pass
