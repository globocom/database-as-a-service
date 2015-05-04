# -*- coding: utf-8 -*-
import logging
from util import full_stack
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0020
from dbaas_flipper.provider import FlipperProvider
LOG = logging.getLogger(__name__)


class CreateFlipper(BaseStep):

    def __unicode__(self):
        return "Creating Flipper MasterPair..."

    def do(self, workflow_dict):
        try:
            databaseinfra = workflow_dict['databaseinfra']
            target_host_one = workflow_dict['source_hosts'][0].future_host.address
            target_host_two = workflow_dict['source_hosts'][1].future_host.address

            target_secondary_ip_one = workflow_dict['source_secondary_ips'][0].equivalent_dbinfraattr.ip
            target_secondary_ip_two = workflow_dict['source_secondary_ips'][1].equivalent_dbinfraattr.ip

            flipper = FlipperProvider()
            LOG.info("Creating Flipper...")
            flipper.create_flipper_dependencies(
                masterpairname=databaseinfra.name,
                hostname1=target_host_one,
                writeip=target_secondary_ip_one,
                readip=target_secondary_ip_two,
                hostname2=target_host_two,
                environment=workflow_dict['target_environment'])

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            LOG.info("Destroying Flipper...")
            flipper = FlipperProvider()
            masterpair_name = workflow_dict['databaseinfra'].name
            environment = workflow_dict['target_environment']

            flipper.destroy_flipper_dependencies(masterpairname=masterpair_name,
                                                 environment=environment)

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
