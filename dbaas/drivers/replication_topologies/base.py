# -*- coding: utf-8 -*-

STOP_RESIZE_START = (
    'workflow.steps.util.resize.stop_vm.StopVM',
    'workflow.steps.util.resize.resize_vm.ResizeVM',
    'workflow.steps.util.resize.start_vm.StartVM',
)


class BaseTopology(object):

    def get_deploy_steps(self):
        raise NotImplementedError()

    def get_clone_steps(self):
        raise NotImplementedError()

    def get_resize_steps(self):
        raise NotImplementedError()

    def get_restore_snapshot_steps(self):
        return (
            'workflow.steps.util.restore_snapshot.restore_snapshot.RestoreSnapshot',
            'workflow.steps.util.restore_snapshot.grant_nfs_access.GrantNFSAccess',
            'workflow.steps.util.restore_snapshot.stop_database.StopDatabase',
            'workflow.steps.util.restore_snapshot.umount_data_volume.UmountDataVolume',
            'workflow.steps.util.restore_snapshot.update_fstab.UpdateFstab',
            'workflow.steps.util.restore_snapshot.mount_data_volume.MountDataVolume',
            'workflow.steps.util.restore_snapshot.start_database.StartDatabase',
            'workflow.steps.util.restore_snapshot.make_export_snapshot.MakeExportSnapshot',
            'workflow.steps.util.restore_snapshot.update_dbaas_metadata.UpdateDbaaSMetadata',
            'workflow.steps.util.restore_snapshot.clean_old_volumes.CleanOldVolumes',
        )

    def get_volume_migration_steps(self):
        return (
            'workflow.steps.util.volume_migration.create_volume.CreateVolume',
            'workflow.steps.util.volume_migration.mount_volume.MountVolume',
            'workflow.steps.util.volume_migration.stop_database.StopDatabase',
            'workflow.steps.util.volume_migration.copy_data.CopyData',
            'workflow.steps.util.volume_migration.umount_volumes.UmountVolumes',
            'workflow.steps.util.volume_migration.update_fstab.UpdateFstab',
            'workflow.steps.util.volume_migration.start_database.StartDatabase',
            'workflow.steps.util.volume_migration.update_dbaas_metadata.UpdateDbaaSMetadata',
        )
