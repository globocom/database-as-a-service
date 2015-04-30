# -*- coding: utf-8 -*-
import logging
from util import full_stack
from workflow.steps.util.base import BaseStep
from dbaas_nfsaas.provider import NfsaasProvider
from workflow.exceptions.error_codes import DBAAS_0020

LOG = logging.getLogger(__name__)


class MakeBackup(BaseStep):

    def __unicode__(self):
        return "Making database backup..."

    def do(self, workflow_dict):
        try:

            databaseinfra = workflow_dict['databaseinfra']
            driver = databaseinfra.get_driver()
            instance = workflow_dict['source_instances'][0]
            client = driver.get_client(instance)

            client.query('show master status')
            r = client.store_result()
            row = r.fetch_row(maxrows=0, how=1)
            workflow_dict['target_binlog_file'] = row[0]['File']
            workflow_dict['target_binlog_pos'] = row[0]['Position']

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
            instance = workflow_dict['source_instances'][0]
            if 'database_locked' in workflow_dict and workflow_dict['database_locked']:
                driver = databaseinfra.get_driver()
                client = driver.get_client(instance)
                driver.unlock_database(client)

            if 'snapshopt_id' in workflow_dict:
                NfsaasProvider.remove_snapshot(environment=databaseinfra.environment,
                                               plan=databaseinfra.plan,
                                               host=instance.hostname,
                                               snapshopt=workflow_dict['snapshopt_id'])

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
