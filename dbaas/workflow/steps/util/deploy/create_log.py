# -*- coding: utf-8 -*-
import logging
from util import full_stack
from system.models import Configuration
from util.laas import register_database_laas
from ..base import BaseStep
from ....exceptions.error_codes import DBAAS_0018

LOG = logging.getLogger(__name__)


class CreateLog(BaseStep):

    def __unicode__(self):
        return "Requesting Log..."

    def do(self, workflow_dict):
        try:
            if Configuration.get_by_name_as_int('laas_integration') == 1:
                register_database_laas(workflow_dict['database'])

            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0018)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Nothing to do here...")
        return True
