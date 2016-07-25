# -*- coding: utf-8 -*-
import logging
from util import full_stack
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0021
from workflow.steps.util.restore_snapshot import use_database_initialization_script
from workflow.steps.mysql.util import start_slave
from physical.models import Instance
from time import sleep


LOG = logging.getLogger(__name__)


class StopDatabase(BaseStep):

    def __unicode__(self):
        return "Stopping database..."

    def do(self, workflow_dict):
        try:
            databaseinfra = workflow_dict['databaseinfra']
            host = workflow_dict['host']
            hosts = [host, ]
            workflow_dict['stoped_hosts'] = []

            hosts.extend(workflow_dict['not_primary_hosts'])

            LOG.debug("HOSTS: {}".format(hosts))
            for host in hosts:
                LOG.info('Stopping database on host {}'.format(host))
                return_code, output = use_database_initialization_script(databaseinfra=databaseinfra,
                                                                         host=host,
                                                                         option='stop')
                if return_code != 0:
                    raise Exception(str(output))

                workflow_dict['stoped_hosts'].append(host)

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0021)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            databaseinfra = workflow_dict['databaseinfra']

            for host in workflow_dict['stoped_hosts']:
                LOG.info('Starting database on host {}'.format(host))
                return_code, output = use_database_initialization_script(databaseinfra=databaseinfra,
                                                                         host=host,
                                                                         option='start')

                if return_code != 0:
                    LOG.warn(str(output))

                instance = host.instance_set.all()[0]
                start_slave(instance=instance)

            LOG.info('Wainting 30 seconds to setting write/read instances')
            sleep(30)
            driver = databaseinfra.get_driver()
            master_host = workflow_dict['host']
            master_instance = Instance.objects.get(hostname=master_host)
            secondary_host = workflow_dict['not_primary_hosts'][0]
            secondary_instance = Instance.objects.get(hostname=secondary_host)
            LOG.info('Setting read on {}'.format(master_instance))
            driver.set_read_ip(instance=master_instance)
            LOG.info('Setting write on {}'.format(secondary_instance))
            driver.set_master(instance=secondary_instance)

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0021)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
