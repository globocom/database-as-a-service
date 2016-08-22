# -*- coding: utf-8 -*-
import logging
from util import full_stack
from backup.models import Snapshot
from workflow.steps.util.base import BaseStep
from workflow.steps.util.nfsaas_utils import create_snapshot, delete_snapshot
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

            driver.lock_database(client)
            workflow_dict['database_locked'] = True
            LOG.debug('Instance %s is locked' % str(instance))

            client.query('show master status')
            r = client.store_result()
            row = r.fetch_row(maxrows=0, how=1)
            workflow_dict['binlog_file'] = row[0]['File']
            workflow_dict['binlog_pos'] = row[0]['Position']

            nfs_snapshot = create_snapshot(
                environment=databaseinfra.environment, host=instance.hostname
            )

            LOG.info('nfs_snapshot: {}'.format(nfs_snapshot))
            if 'error' in nfs_snapshot:
                errormsg = nfs_snapshot['error']
                raise Exception(errormsg)

            if 'id' in nfs_snapshot and 'name' in nfs_snapshot:
                workflow_dict['snapshopt_id'] = nfs_snapshot['id']
                workflow_dict['snapshot_name'] = nfs_snapshot['name']
            else:
                errormsg = 'There is no snapshot information'
                raise Exception(errormsg)

            driver.unlock_database(client)
            workflow_dict['database_locked'] = False

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            from dbaas_nfsaas.models import HostAttr

            databaseinfra = workflow_dict['databaseinfra']
            instance = workflow_dict['source_instances'][0]
            if 'database_locked' in workflow_dict and workflow_dict['database_locked']:
                driver = databaseinfra.get_driver()
                client = driver.get_client(instance)
                driver.unlock_database(client)

            if 'snapshopt_id' in workflow_dict:
                snapshot = Snapshot.objects.get(
                    snapshopt_id=workflow_dict['snapshopt_id']
                )
                delete_snapshot(snapshot=snapshot)

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
