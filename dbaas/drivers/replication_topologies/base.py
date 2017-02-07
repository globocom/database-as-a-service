# -*- coding: utf-8 -*-

STOP_RESIZE_START = (
    'workflow.steps.util.resize.stop_vm.StopVM',
    'workflow.steps.util.resize.resize_vm.ResizeVM',
    'workflow.steps.util.resize.start_vm.StartVM',
)


class BaseTopology(object):

    def deploy_first_steps(self):
        raise NotImplementedError()

    def deploy_last_steps(self):
        raise NotImplementedError()

    def monitoring_steps(self):
        return (
            'workflow.steps.util.deploy.create_zabbix.CreateZabbix',
            'workflow.steps.util.deploy.create_dbmonitor.CreateDbMonitor',
        )

    def get_deploy_steps(self):
        return self.deploy_first_steps() + self.monitoring_steps() + self.deploy_last_steps()

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

    def get_upgrade_steps(self):
        return [
            (
                'workflow.steps.util.upgrade.vm.ChangeMaster',
                'workflow.steps.util.upgrade.zabbix.DestroyAlarms',
                'workflow.steps.util.upgrade.db_monitor.DisableMonitoring',
                'workflow.steps.util.upgrade.database.Stop',
                'workflow.steps.util.upgrade.database.CheckIsDown',
                'workflow.steps.util.upgrade.vm.Stop',
                'workflow.steps.util.upgrade.vm.InstallNewTemplate',
                'workflow.steps.util.upgrade.vm.Start',
                'workflow.steps.util.upgrade.vm.WaitingBeReady',
                'workflow.steps.util.upgrade.vm.UpdateOSDescription',
                'workflow.steps.util.upgrade.plan.Initialization',
                'workflow.steps.util.upgrade.plan.Configure',
                'workflow.steps.util.upgrade.pack.Configure',
            ) + self.get_upgrade_steps_extra() + (
                'workflow.steps.util.upgrade.database.Start',
                'workflow.steps.util.upgrade.database.CheckIsUp',
            ),
        ] + self.get_upgrade_steps_final()

    def get_upgrade_steps_extra(self):
        return tuple()

    def get_upgrade_steps_final(self):
        return [
            (
                'workflow.steps.util.upgrade.db_monitor.EnableMonitoring',
                'workflow.steps.util.upgrade.zabbix.CreateAlarms',
            ),
        ]
