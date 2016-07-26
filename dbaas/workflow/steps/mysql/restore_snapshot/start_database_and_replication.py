# -*- coding: utf-8 -*-
import logging
from util import full_stack
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0020
from workflow.steps.mysql.util import get_replication_information_from_file
from workflow.steps.util.restore_snapshot import use_database_initialization_script
from workflow.steps.mysql.util import change_master_to
from workflow.steps.mysql.util import start_slave
from physical.models import Instance
from time import sleep

LOG = logging.getLogger(__name__)


class StartDatabaseAndReplication(BaseStep):

    def __unicode__(self):
        return "Changing master..."

    def do(self, workflow_dict):
        try:

            databaseinfra = workflow_dict['databaseinfra']

            master_host = workflow_dict['host']
            master_instance = Instance.objects.get(hostname=master_host)

            secondary_host = workflow_dict['not_primary_hosts'][0]
            secondary_instance = Instance.objects.get(hostname=secondary_host)

            master_log_file, master_log_pos = get_replication_information_from_file(
                host=master_host)

            return_code, output = use_database_initialization_script(databaseinfra=databaseinfra,
                                                                     host=master_host,
                                                                     option='start')
            if return_code != 0:
                raise Exception(str(output))

            return_code, output = use_database_initialization_script(databaseinfra=databaseinfra,
                                                                     host=secondary_host,
                                                                     option='start')
            if return_code != 0:
                raise Exception(str(output))

            LOG.info("Waiting 1 minute to continue")
            sleep(60)

            change_master_to(instance=master_instance,
                             master_host=secondary_host.address,
                             bin_log_file=master_log_file,
                             bin_log_position=master_log_pos)

            change_master_to(instance=secondary_instance,
                             master_host=master_host.address,
                             bin_log_file=master_log_file,
                             bin_log_position=master_log_pos)

            start_slave(instance=master_instance)
            start_slave(instance=secondary_instance)

            LOG.info("Waiting 30 seconds to continue")
            sleep(30)
            driver = databaseinfra.get_driver()
            driver.set_read_ip(instance=master_instance)
            driver.set_master(instance=secondary_instance)

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
            host = workflow_dict['host']
            hosts = [host, ]
            hosts.extend(workflow_dict['not_primary_hosts'])

            LOG.debug("HOSTS: {}".format(hosts))
            for host in hosts:
                return_code, output = use_database_initialization_script(databaseinfra=databaseinfra,
                                                                         host=host,
                                                                         option='stop')
                if return_code != 0:
                    LOG.info(str(output))

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
