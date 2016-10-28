# -*- coding: utf-8 -*-
import logging
from util import full_stack
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0020
from workflow.steps.mysql.util import get_client_for_infra

LOG = logging.getLogger(__name__)


class SetMasterReadOnly(BaseStep):

    def __unicode__(self):
        return "Setting master to read only..."

    def do(self, workflow_dict):
        try:
            client = get_client_for_infra(
                databaseinfra=workflow_dict['databaseinfra'])
            client.query("set global read_only='ON'")

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            client = get_client_for_infra(
                databaseinfra=workflow_dict['databaseinfra'])
            client.query("set global read_only='OFF'")

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
