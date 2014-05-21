# -*- coding: utf-8 -*-
from client import DNSAPI
from models import DatabaseInfraDNSList
from django.db import transaction
import string
import random
import logging

LOG = logging.getLogger(__name__)


class DNSAPIProvider(object):
    
    @classmethod
    def create_dns(self, dnsapi, name, ip, domain):
        
        LOG.info('Create dns %s.%s to IP %s' % (name, domain, ip))
        domain_id = dnsapi.get_domain_id_by_name(domain=domain)
        if domain_id is None:
            LOG.error('Domain %s not found!' % domain)
            return None
        
        record_id = dnsapi.get_record_by_name(name=name, domain_id=domain_id)
        
        cont = 0
        while record_id:
            LOG.warning('DNS %s.%s alredy exists!' % (name, domain))
            name = '%s%s' % (name, random.choice(string.letters))
            record_id = dnsapi.get_record_by_name(name=name, domain_id=domain_id)
            if cont > 10:
                LOG.error('Could not create dns %s.%s, it already exists!' % (name, domain))
                return None
            cont += 1
        
        dnsapi.create_record(name=name, content=ip, domain_id=domain_id)
        
        dns = '%s.%s' % (name, domain)
        LOG.info('DNS %s successfully created.' % dns)
        return dns
        
    @classmethod
    def delete_dns(self, dnsapi, name, domain):
        
        dns = '%s.%s' % (name, domain)
        LOG.info('Delete dns %s' % (dns))
        
        domain_id = dnsapi.get_domain_id_by_name(domain=domain)
        if domain_id is None:
            LOG.error('Domain %s not found!' % domain)
            return None
        
        record_id = dnsapi.get_record_by_name(name=name, domain_id=domain_id)
        
        dnsapi.delete_record(record_id)
        LOG.info('DNS %s successfully deleted.' % dns)
        
        return True
        
    @classmethod
    @transaction.commit_on_success
    def create_database_dns(self, databaseinfra):
        
        dnsapi = DNSAPI(environment = databaseinfra.environment)
        
        for databaseinfradnslist in DatabaseInfraDNSList.objects.filter(databaseinfra=databaseinfra.id):
            dns = self.create_dns(dnsapi=dnsapi, name=databaseinfradnslist.name, ip=databaseinfradnslist.ip, domain=databaseinfradnslist.domain)
            if dns:
                databaseinfradnslist.dns = dns
                databaseinfradnslist.save()
        
        dnsapi.export(now=False)
        
    @classmethod
    @transaction.commit_on_success
    def remove_database_dns(self, environment, databaseinfraid):
        
        dnsapi = DNSAPI(environment = environment)
        
        for databaseinfradnslist in DatabaseInfraDNSList.objects.filter(databaseinfra=databaseinfraid):
            name = databaseinfradnslist.dns.split('.' + databaseinfradnslist.domain)[0]
            ret = self.delete_dns(dnsapi = dnsapi, name = name, domain = databaseinfradnslist.domain)
            if ret:
                databaseinfradnslist.delete()
        
        dnsapi.export(now=False)