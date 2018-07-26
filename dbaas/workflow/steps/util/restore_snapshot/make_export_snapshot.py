# -*- coding: utf-8 -*-
import logging
from util import full_stack
from backup.models import BackupGroup
from backup.tasks import mysql_binlog_save
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0021
from workflow.steps.util.restore_snapshot import make_host_backup

LOG = logging.getLogger(__name__)


class MakeExportSnapshot(BaseStep):

    def __unicode__(self):
        return "Making export snapshot..."

    def do(self, workflow_dict):
        try:
            group = BackupGroup()
            group.save()

            for host_and_export in workflow_dict['hosts_and_exports']:
                host = host_and_export['host']
                export_id = host_and_export['old_export_id']

                ret = make_host_backup(
                    database=workflow_dict['database'],
                    instance=host.instances.all()[0],
                    export_id=export_id,
                    group=group
                )
                if not ret:
                    msg = 'Could not make snapshot for export_id: {} on host {}'.format(
                        export_id, host)
                    LOG.error(msg)
                    raise Exception(msg)

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0021)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0021)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False


class MySQLSaveBinlogPosition(BaseStep):

    def __unicode__(self):
        return "Saving bing log position..."

    def do(self, workflow_dict):
        for host_and_export in workflow_dict['hosts_and_exports']:
            instance = host_and_export['host'].instances.first()
            driver = workflow_dict['database'].infra.get_driver()
            client = driver.get_client(instance)
            mysql_binlog_save(client, instance)

        return True

    def undo(self, workflow_dict):
        return True
