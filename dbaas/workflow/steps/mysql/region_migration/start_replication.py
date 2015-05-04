# -*- coding: utf-8 -*-
import logging
from util import full_stack
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0020
from workflow.steps.mysql.util import get_replication_info
from workflow.steps.mysql.util import change_master_to

LOG = logging.getLogger(__name__)


class StartReplication(BaseStep):

    def __unicode__(self):
        return "Starting Replication..."

    def do(self, workflow_dict):
        try:
            master_source_instance = workflow_dict['source_instances'][0]

            master_target_instance = workflow_dict['source_instances'][0].future_instance
            slave_target_instance = workflow_dict['source_instances'][1].future_instance

            master_log_file, master_log_pos = get_replication_info(master_target_instance)

            change_master_to(instance=master_target_instance,
                             master_host=master_source_instance.address,
                             bin_log_file=workflow_dict['binlog_file'],
                             bin_log_position=workflow_dict['binlog_pos'])

            change_master_to(instance=slave_target_instance,
                             master_host=master_target_instance.address,
                             bin_log_file=master_log_file,
                             bin_log_position=master_log_pos)

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
