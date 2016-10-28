# -*- coding: utf-8 -*-
import logging
import datetime
from util import full_stack
from backup.models import Snapshot
from logical.models import Database
from dbaas_nfsaas.models import HostAttr as Nfsaas_HostAttr
from workflow.steps.util.base import BaseStep
from workflow.steps.util.nfsaas_utils import create_snapshot, delete_snapshot
from workflow.exceptions.error_codes import DBAAS_0020

LOG = logging.getLogger(__name__)


class MakeBackup(BaseStep):

    def __unicode__(self):
        return "Making database backup..."

    def set_backup_error(snapshot, errormsg):
        LOG.error(errormsg)
        snapshot.status = Snapshot.ERROR
        snapshot.error = errormsg
        snapshot.size = 0
        snapshot.end_at = datetime.datetime.now()
        snapshot.purge_at = datetime.datetime.now()
        snapshot.save()

    def do(self, workflow_dict):
        try:

            databaseinfra = workflow_dict['databaseinfra']
            driver = databaseinfra.get_driver()
            instance = workflow_dict['source_instances'][0]
            client = driver.get_client(instance)

            snapshot = Snapshot()
            snapshot.start_at = datetime.datetime.now()
            snapshot.type = Snapshot.SNAPSHOPT
            snapshot.status = Snapshot.RUNNING
            snapshot.instance = instance
            snapshot.environment = databaseinfra.environment
            snapshot.status = Snapshot.SUCCESS

            nfsaas_hostattr = Nfsaas_HostAttr.objects.get(
                host=instance.hostname, is_active=True)
            snapshot.export_path = nfsaas_hostattr.nfsaas_path

            databases = Database.objects.filter(
                databaseinfra=instance.databaseinfra)
            if databases:
                snapshot.database_name = databases[0].name

            snapshot.save()

            driver.lock_database(client)
            workflow_dict['database_locked'] = True
            LOG.debug('Instance %s is locked' % str(instance))

            client.query('show master status')
            r = client.store_result()
            row = r.fetch_row(maxrows=0, how=1)
            workflow_dict['binlog_file'] = row[0]['File']
            workflow_dict['binlog_pos'] = row[0]['Position']

            try:
                nfs_snapshot = create_snapshot(
                    environment=databaseinfra.environment,
                    host=instance.hostname
                )
            except Exception as e:
                errormsg = "Error creating snapshot: {}".format(e)
                self.set_backup_error(snapshot, errormsg)
                raise Exception(errormsg)
            finally:
                LOG.debug('Unlocking instance %s' % str(instance))
                driver.unlock_database(client)
                workflow_dict['database_locked'] = False

            LOG.info('nfs_snapshot: {}'.format(nfs_snapshot))
            if 'error' in nfs_snapshot:
                errormsg = nfs_snapshot['error']
                self.set_backup_error(snapshot, errormsg)
                raise Exception(errormsg)

            if 'id' in nfs_snapshot and 'name' in nfs_snapshot:
                workflow_dict['snapshopt_id'] = nfs_snapshot['id']
                workflow_dict['snapshot_name'] = nfs_snapshot['name']

                snapshot.snapshopt_id = nfs_snapshot['id']
                snapshot.snapshot_name = nfs_snapshot['name']
                snapshot.status = Snapshot.SUCCESS
                snapshot.end_at = datetime.datetime.now()
                snapshot.save()

            else:
                errormsg = 'There is no snapshot information'
                self.set_backup_error(snapshot, errormsg)
                raise Exception(errormsg)

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:

            if 'snapshopt_id' in workflow_dict:
                snapshot = Snapshot.objects.get(
                    snapshopt_id=workflow_dict['snapshopt_id']
                )
                delete_snapshot(snapshot=snapshot)
                snapshot.purge_at = datetime.datetime.now()
                snapshot.save()

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
