# -*- coding: utf-8 -*-
import logging
from util import full_stack
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0020
from workflow.steps.redis.util import change_slave_priority_file
from workflow.steps.redis.util import change_slave_priority_instance
from workflow.steps.redis.util import failover_sentinel
from time import sleep


LOG = logging.getLogger(__name__)


class SwitchMaster(BaseStep):

    def __unicode__(self):
        return "Switching master..."

    def do(self, workflow_dict):
        try:

            databaseinfra = workflow_dict['databaseinfra']
            driver = databaseinfra.get_driver()

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

            attempts = 1
            max_attempts = 10
            while True:

                sentinel_instance = driver.get_non_database_instances()[0]
                failover_sentinel(host=sentinel_instance.hostname,
                                  sentinel_host=sentinel_instance.address,
                                  sentinel_port=sentinel_instance.port,
                                  service_name=databaseinfra.name)

                sleep(30)

                sentinel_client = driver.get_sentinel_client(sentinel_instance)
                master_address = sentinel_client.discover_master(databaseinfra.name)[0]

                target_is_master = False
                for source_instance in workflow_dict['source_instances']:
                    target_instance = source_instance.future_instance
                    if target_instance.address == master_address:
                        target_is_master = True
                        LOG.info("{} is master".format(target_instance))
                        break

                if target_is_master:
                    break

                if attempts >= max_attempts:
                    raise Exception('It could not switch the master.')

                attempts += 1
                LOG.info("There was something wrong in sentinel failover.")
                LOG.info("Trying again ( {} of {} )".format(attempts, max_attempts))

            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:

            databaseinfra = workflow_dict['databaseinfra']
            driver = databaseinfra.get_driver()

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

            attempts = 1
            max_attempts = 10
            while True:

                sentinel_instance = driver.get_non_database_instances()[0]
                failover_sentinel(host=sentinel_instance.hostname,
                                  sentinel_host=sentinel_instance.address,
                                  sentinel_port=sentinel_instance.port,
                                  service_name=databaseinfra.name)

                sleep(30)

                sentinel_client = driver.get_sentinel_client(sentinel_instance)
                master_address = sentinel_client.discover_master(databaseinfra.name)[0]

                source_is_master = False
                for source_instance in workflow_dict['source_instances']:
                    if source_instance.address == master_address:
                        source_is_master = True
                        LOG.info("{} is master".format(source_instance))
                        break

                if source_is_master:
                    break

                if attempts >= max_attempts:
                    raise Exception('It could not switch the master.')

                attempts += 1
                LOG.info("There was something wrong in sentinel failover.")
                LOG.info("Trying again ( {} of {} )".format(attempts, max_attempts))

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
