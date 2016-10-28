# -*- coding: utf-8 -*-
import logging
import datetime
from util import full_stack
from backup.models import Snapshot
from workflow.steps.util.nfsaas_utils import delete_snapshot
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0020

LOG = logging.getLogger(__name__)


class RemoveNfsSnapshot(BaseStep):

    def __unicode__(self):
        return "Removing nfs snapshot..."

    def do(self, workflow_dict):
        try:
            if 'snapshopt_id' in workflow_dict:
                snapshot = Snapshot.objects.get(
                    snapshopt_id=workflow_dict['snapshopt_id']
                )
                delete_snapshot(snapshot=snapshot)
                snapshot.purge_at = datetime.datetime.now()
                snapshot.save()

            del workflow_dict['snapshopt_id']

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
