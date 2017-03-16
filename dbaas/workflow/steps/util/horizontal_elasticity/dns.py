# -*- coding: utf-8 -*-
import logging
from workflow.steps.util.base import BaseInstanceStep
from dbaas_dnsapi.utils import add_dns_record
from dbaas_dnsapi.provider import DNSAPIProvider
from dbaas_dnsapi.models import HOST
from dbaas_dnsapi.models import INSTANCE

LOG = logging.getLogger(__name__)


class DNSStep(BaseInstanceStep):

    def __init__(self, instance):
        super(DNSStep, self).__init__(instance)

        self.databaseinfra = self.instance.databaseinfra
        self.environment = self.databaseinfra.environment

    def do(self):
        raise NotImplementedError

    def undo(self):
        pass


class CreateDNS(DNSStep):

    def __unicode__(self):
        return "Creating DNS..."

    def do(self):
        LOG.info('Creating DNS for {}'.format(self.instance))

        host = self.instance.hostname
        host.hostname = add_dns_record(
            databaseinfra=self.databaseinfra,
            name=self.instance.vm_name,
            ip=host.address,
            type=HOST)
        host.save()

        self.instance.dns = add_dns_record(
            databaseinfra=self.databaseinfra,
            name=self.instance.vm_name,
            ip=self.instance.address,
            type=INSTANCE)
        self.instance.save()

        DNSAPIProvider.create_database_dns_for_ip(
            databaseinfra=self.databaseinfra,
            ip=self.instance.address)

    def undo(self):
        LOG.info('Running undo of CreateDNS')

        DNSAPIProvider.remove_databases_dns_for_ip(
            databaseinfra=self.databaseinfra,
            ip=self.instance.address)
