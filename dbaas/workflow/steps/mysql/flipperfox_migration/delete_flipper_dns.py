# -*- coding: utf-8 -*-
import logging
from util import full_stack
from dbaas_dnsapi.provider import DNSAPIProvider
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0020

LOG = logging.getLogger(__name__)


class DeleteFlipperDNS(BaseStep):

    def __unicode__(self):
        return "Deleting Flipper DNS..."

    def do(self, workflow_dict):
        try:

            for infra_attr in workflow_dict['source_secondary_ips']:
                if not infra_attr.is_write:
                    LOG.info("Calling dnsapi provider...")
                    DNSAPIProvider.remove_database_dns(
                        environment=workflow_dict['environment'],
                        databaseinfraid=workflow_dict['databaseinfra'].id,
                        dns=infra_attr.dns)

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):

        LOG.info("Running undo - nothing to do here...")
        return True
