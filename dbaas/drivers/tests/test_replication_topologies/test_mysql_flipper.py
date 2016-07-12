# -*- coding: utf-8 -*-
from drivers.replication_topologies.mysql_flipper import MySQLFlipper
from drivers.tests.test_replication_topologies.test_mysql_single import TestMySQLSingleSettings


class TestMySQLFlipper(TestMySQLSingleSettings):

    def _get_replication_topology_driver(self):
        return MySQLFlipper()

    def _get_restore_snapshot_settings(self):
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
