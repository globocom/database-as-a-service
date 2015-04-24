# -*- coding: utf-8 -*-
import logging
from util import full_stack
from ...util.base import BaseStep
from ....exceptions.error_codes import DBAAS_0019

LOG = logging.getLogger(__name__)


class RemoveInstancesReplicaSet(BaseStep):

    def __unicode__(self):
        return "Removing instances from Replica Set..."

    def do(self, workflow_dict):
        try:

            from time import sleep
            sleep(30)
            raise Exception('Test')
            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0019)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0019)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
