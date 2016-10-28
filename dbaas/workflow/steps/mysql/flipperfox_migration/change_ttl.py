# -*- coding: utf-8 -*-
import logging
from util import full_stack
from dbaas_dnsapi.provider import DNSAPIProvider
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0020

LOG = logging.getLogger(__name__)


class DecreaseTTL(BaseStep):

    def __unicode__(self):
        return "Changing TTL..."

    def do(self, workflow_dict):
        try:

            LOG.info("Calling dnsapi provider...")
            DNSAPIProvider.update_database_dns_ttl(
                databaseinfra=workflow_dict['databaseinfra'], ttl=60)

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:

            DNSAPIProvider.update_database_dns_ttl(
                databaseinfra=workflow_dict['databaseinfra'], ttl=None)
            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False


class DefaultTTL(BaseStep):

    def __unicode__(self):
        return "Changing TTL..."

    def do(self, workflow_dict):
        try:

            LOG.info("Calling dnsapi provider...")
            DNSAPIProvider.update_database_dns_ttl(
                databaseinfra=workflow_dict['databaseinfra'], ttl=None)

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):

        LOG.info("Running undo - nothing to do here...")
        return True
