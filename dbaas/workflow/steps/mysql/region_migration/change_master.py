# -*- coding: utf-8 -*-
import logging
from util import full_stack
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0020
from workflow.steps.mysql.util import get_replication_info
from workflow.steps.mysql.util import change_master_to

LOG = logging.getLogger(__name__)


class ChangeMaster(BaseStep):

    def __unicode__(self):
        return "Changing master..."

    def do(self, workflow_dict):
        try:
            target_instances = workflow_dict[
                'databaseinfra'].instances.filter(future_instance=None)

            target_instance_one = target_instances[1]
            target_instance_zero = target_instances[0]

            source_instance_zero = workflow_dict['source_instances'][0]

            master_log_file, master_log_pos = get_replication_info(
                target_instance_one)
            change_master_to(instance=target_instance_zero,
                             master_host=target_instance_one.address,
                             bin_log_file=master_log_file,
                             bin_log_position=master_log_pos)

            master_log_file, master_log_pos = get_replication_info(
                target_instance_zero)
            change_master_to(instance=source_instance_zero,
                             master_host=target_instance_zero.address,
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
            target_instances = workflow_dict[
                'databaseinfra'].instances.filter(future_instance=None)

            target_instance_zero = target_instances[0]

            source_instance_zero = workflow_dict['source_instances'][0]
            source_instance_one = workflow_dict['source_instances'][1]

            master_log_file, master_log_pos = get_replication_info(
                source_instance_one)
            change_master_to(instance=source_instance_zero,
                             master_host=source_instance_one.address,
                             bin_log_file=master_log_file,
                             bin_log_position=master_log_pos)

            master_log_file, master_log_pos = get_replication_info(
                source_instance_zero)
            change_master_to(instance=target_instance_zero,
                             master_host=source_instance_zero.address,
                             bin_log_file=master_log_file,
                             bin_log_position=master_log_pos)
            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
