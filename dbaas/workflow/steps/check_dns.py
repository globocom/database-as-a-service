# -*- coding: utf-8 -*-
import logging
from base import BaseStep
from dbaas_dnsapi.models import DatabaseInfraDNSList
from dbaas_credentials.models import CredentialType
from util import check_nslookup, get_credentials_for


LOG = logging.getLogger(__name__)


class CheckDns(BaseStep):

    def __unicode__(self):
        return "Checking dns..."

    def do(self, workflow_dict):
        try:

            if not 'databaseinfra' in workflow_dict:
                return False

            dns_credentials = get_credentials_for(environment=workflow_dict['environment'], credential_type= CredentialType.DNSAPI)

            dns_list = DatabaseInfraDNSList.objects.filter(databaseinfra= workflow_dict['databaseinfra'].id)

            for dns in dns_list:
                LOG.info("Checking dns %s on %s" % (dns.dns, dns_credentials.project))
                check_nslookup(dns.dns, dns_credentials.project)

            return True
        except Exception, e:
            print e
            return False

    def undo(self, workflow_dict):
        LOG.info("Nothing to do here...")
        return True
