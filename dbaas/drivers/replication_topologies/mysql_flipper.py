# -*- coding: utf-8 -*-
import logging
from dbaas import util
from mysql_single import MySQLSingle
from dbaas_cloudstack.models import HostAttr

LOG = logging.getLogger(__name__)


class MySQLFlipper(MySQLSingle):

    def get_restore_snapshot_steps(self):
        return (
            'workflow.steps.mysql.restore_snapshot.restore_snapshot.RestoreSnapshot',
            'workflow.steps.util.restore_snapshot.grant_nfs_access.GrantNFSAccess',
            'workflow.steps.mysql.restore_snapshot.stop_database.StopDatabase',
            'workflow.steps.mysql.restore_snapshot.umount_data_volume.UmountDataVolume',
            'workflow.steps.util.restore_snapshot.update_fstab.UpdateFstab',
            'workflow.steps.util.restore_snapshot.mount_data_volume.MountDataVolume',
            'workflow.steps.mysql.restore_snapshot.start_database_and_replication.StartDatabaseAndReplication',
            'workflow.steps.util.restore_snapshot.make_export_snapshot.MakeExportSnapshot',
            'workflow.steps.util.restore_snapshot.update_dbaas_metadata.UpdateDbaaSMetadata',
            'workflow.steps.util.restore_snapshot.clean_old_volumes.CleanOldVolumes',
        )

    def switch_master(self, driver):
        master = driver.get_master_instance()
        slave = driver.get_slave_instances()[0]
        host = master.hostname

        host_attr = HostAttr.objects.get(host=host)

        script = """
        sudo -u flipper /usr/bin/flipper {{MASTERPAIRNAME}} set write {{HOST01.address}}
        sudo -u flipper /usr/bin/flipper {{MASTERPAIRNAME}} set read {{HOST02.address}}
        """

        context_dict = {
            'MASTERPAIRNAME': driver.databaseinfra.name,
            'HOST01': slave.hostname,
            'HOST02': master.hostname,
        }
        script = util.build_context_script(context_dict, script)
        output = {}

        return_code = util.exec_remote_command(
            server=host.address, username=host_attr.vm_user,
            password=host_attr.vm_password, command=script, output=output
        )

        LOG.info(output)
        if return_code != 0:
            raise Exception(str(output))
