# -*- coding: utf-8 -*-
import logging
from util import full_stack
from util import exec_remote_command
from util import build_context_script
from dbaas_cloudstack.models import HostAttr as CS_HostAttr
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0023
from backup.tasks import make_instance_snapshot_backup


LOG = logging.getLogger(__name__)


class TakeInstanceBackup(BaseStep):

    def __unicode__(self):
        return "Taking instance backup ..."

    def do(self, workflow_dict):
        try:

            instance = workflow_dict['instances'][0]

            error = {}
            if make_instance_snapshot_backup(instance=instance, error=error):
                msg = "Backup for %s was successful" % (str(instance))
                LOG.info(msg)
            else:
                msg = "Backup for %s was unsuccessful. Error: %s" % (str(instance), error['errormsg'])
                LOG.error(msg)
                raise Exception(msg)

            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0023)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        try:
            pass

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0023)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
