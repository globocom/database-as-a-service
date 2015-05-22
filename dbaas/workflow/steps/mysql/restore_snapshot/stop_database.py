# -*- coding: utf-8 -*-
import logging
from util import full_stack
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0021
from workflow.steps.util.restore_snapshot import use_database_initialization_script
from workflow.steps.mysql.util import start_slave
from workflow.steps.mysql.util import set_infra_read_ip
from workflow.steps.mysql.util import set_infra_write_ip
from time import sleep


LOG = logging.getLogger(__name__)


class StopDatabase(BaseStep):

    def __unicode__(self):
        return "Stoping database..."

    def do(self, workflow_dict):
        try:
            databaseinfra = workflow_dict['databaseinfra']
            host = workflow_dict['host']
            hosts = [host, ]
            workflow_dict['stoped_hosts'] = []

            hosts.extend(workflow_dict['not_primary_hosts'])

            LOG.debug("HOSTS: {}".format(hosts))
            for host in hosts:
                LOG.info('Stoping database on host {}'.format(host))
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

            LOG.info('Wainting 30 seconds to setting flipper IPs')
            sleep(30)
            LOG.info('Setting read IP on {}'.format(workflow_dict['host']))
            set_infra_read_ip(slave_host=workflow_dict['host'],
                              infra_name=databaseinfra.name)

            LOG.info('Setting write IP on {}'.format(workflow_dict['not_primary_hosts'][0]))
            set_infra_write_ip(master_host=workflow_dict['not_primary_hosts'][0],
                               infra_name=databaseinfra.name)

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0021)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
