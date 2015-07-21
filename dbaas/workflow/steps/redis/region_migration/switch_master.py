# -*- coding: utf-8 -*-
import logging
from util import full_stack
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0020
from workflow.steps.redis.util import change_slave_priority_file
from workflow.steps.redis.util import change_slave_priority_instance
from workflow.steps.redis.util import failover_sentinel


LOG = logging.getLogger(__name__)


class SwitchMaster(BaseStep):

    def __unicode__(self):
        return "Starting database and replication..."

    def do(self, workflow_dict):
        try:

            for source_instance in workflow_dict['source_instances']:
                if source_instance.instance_type == source_instance.REDIS:
                    source_host = source_instance.hostname
                    change_slave_priority_file(
                        host=source_host, original_value=100, final_value=0)
                    change_slave_priority_instance(
                        instance=source_instance, final_value=0)

                    target_instance = source_instance.future_instance
                    target_host = target_instance.hostname
                    change_slave_priority_file(
                        host=target_host, original_value=0, final_value=100)
                    change_slave_priority_instance(
                        instance=target_instance, final_value=100)

            for source_instance in workflow_dict['source_instances']:
                if source_instance.instance_type == source_instance.REDIS_SENTINEL:
                    failover_sentinel(host=source_instance.hostname,
                                      sentinel_host=source_instance.address,
                                      sentinel_port=source_instance.port,
                                      service_name=workflow_dict['databaseinfra'].name)
                    break

            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:

            for source_instance in workflow_dict['source_instances']:
                if source_instance.instance_type == source_instance.REDIS:
                    source_host = source_instance.hostname
                    change_slave_priority_file(
                        host=source_host, original_value=0, final_value=100)
                    change_slave_priority_instance(
                        instance=source_instance, final_value=100)

                    target_instance = source_instance.future_instance
                    target_host = target_instance.hostname
                    change_slave_priority_file(
                        host=target_host, original_value=100, final_value=0)
                    change_slave_priority_instance(
                        instance=target_instance, final_value=0)

            for source_instance in workflow_dict['source_instances']:
                if source_instance.instance_type == source_instance.REDIS_SENTINEL:
                    failover_sentinel(host=source_instance.hostname,
                                      sentinel_host=source_instance.address,
                                      sentinel_port=source_instance.port,
                                      service_name=workflow_dict['databaseinfra'].name)
                    break

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
