# -*- coding: utf-8 -*-
import logging
from util import full_stack
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0020
from dbaas_flipper.provider import FlipperProvider
LOG = logging.getLogger(__name__)


class RenameFlipperMasterPair(BaseStep):

    def __unicode__(self):
        return "Renaming flipper master pair..."

    def do(self, workflow_dict):
        try:
            environment = workflow_dict['source_environment']
            databaseinfra = workflow_dict['databaseinfra']

            new_name = "old_" + databaseinfra.name

            flipper = FlipperProvider()
            flipper.rename_masterpairname(masterpairname=databaseinfra.name,
                                          masterpairnewname=new_name,
                                          environment=environment)

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            environment = workflow_dict['source_environment']
            databaseinfra = workflow_dict['databaseinfra']

            old_name = "old_" + databaseinfra.name

            flipper = FlipperProvider()
            flipper.rename_masterpairname(masterpairname=old_name,
                                          masterpairnewname=databaseinfra.name,
                                          environment=environment)

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
