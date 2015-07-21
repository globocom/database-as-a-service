# -*- coding: utf-8 -*-
import logging
from util import full_stack
from dbaas_cloudstack.models import DatabaseInfraOffering
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0020

LOG = logging.getLogger(__name__)


class UpdateDBaaSMetadata(BaseStep):

    def __unicode__(self):
        return "Updating DBaaS Metadata..."

    def do(self, workflow_dict):
        try:

            databaseinfra = workflow_dict['databaseinfra']
            databaseinfra.environment = workflow_dict['target_environment']
            databaseinfra.plan = workflow_dict['target_plan']
            databaseinfra.save()
            database = workflow_dict['database']
            database.environment = workflow_dict['target_environment']
            database.save()

            dbinfraoffering = DatabaseInfraOffering.objects.get(
                databaseinfra=databaseinfra)
            dbinfraoffering.offering = workflow_dict['target_offering']
            dbinfraoffering.save()

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:

            databaseinfra = workflow_dict['databaseinfra']
            databaseinfra.environment = workflow_dict['source_environment']
            databaseinfra.plan = workflow_dict['source_plan']
            databaseinfra.save()
            database = workflow_dict['database']
            database.environment = workflow_dict['source_environment']
            database.save()

            dbinfraoffering = DatabaseInfraOffering.objects.get(
                databaseinfra=databaseinfra)
            dbinfraoffering.offering = workflow_dict['source_offering']
            dbinfraoffering.save()

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
