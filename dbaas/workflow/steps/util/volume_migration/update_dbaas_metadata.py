# -*- coding: utf-8 -*-
import logging
from util import full_stack
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0021

LOG = logging.getLogger(__name__)


class UpdateDbaaSMetadata(BaseStep):

    def __unicode__(self):
        return "Updating dbaas metadata..."

    def do(self, workflow_dict):
        try:
            volume = workflow_dict['volume']
            old_volume = workflow_dict['old_volume']

            old_volume.is_active = False
            old_volume.save()

            volume.is_active = True
            volume.save()

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0021)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            volume = workflow_dict['volume']
            old_volume = workflow_dict['old_volume']

            old_volume.is_active = True
            old_volume.save()

            volume.is_active = False
            volume.save()

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0021)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
