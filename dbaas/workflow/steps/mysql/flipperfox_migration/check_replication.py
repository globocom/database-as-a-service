# -*- coding: utf-8 -*-
import logging
from util import full_stack
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0020
from workflow.steps.mysql.util import check_seconds_behind

LOG = logging.getLogger(__name__)


class CheckReplication(BaseStep):

    def __unicode__(self):
        return "Checking replication..."

    def do(self, workflow_dict):
        try:

            msg = "Replication check maximum attempts for instance {}"
            for source_instance in workflow_dict['source_instances']:

                if not check_seconds_behind(source_instance):
                    raise Exception(msg.format(source_instance))

                target_instance = source_instance.future_instance
                if not check_seconds_behind(target_instance):
                    raise Exception(msg.format(target_instance))

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
