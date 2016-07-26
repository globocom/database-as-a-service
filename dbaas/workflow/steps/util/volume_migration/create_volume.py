# -*- coding: utf-8 -*-
import logging
from util import full_stack
from workflow.steps.util.base import BaseStep
from workflow.steps.util.nfsaas_utils import create_disk, delete_disk
from workflow.exceptions.error_codes import DBAAS_0022

LOG = logging.getLogger(__name__)


class CreateVolume(BaseStep):

    def __unicode__(self):
        return "Requesting NFS volume..."

    def do(self, workflow_dict):
        try:
            environment = workflow_dict['environment']
            plan = workflow_dict['plan']

            host = workflow_dict['host']
            LOG.info("Creating nfsaas volume...")

            volume = create_disk(environment=environment, host=host, plan=plan)
            if not volume:
                return False

            workflow_dict['volume'] = volume

            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0022)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        try:
            if 'volume' in workflow_dict:
                LOG.info("Destroying NFS volume...")
                delete_disk(
                    environment=workflow_dict['environment'],
                    host=workflow_dict['volume'].host
                )

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0022)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
