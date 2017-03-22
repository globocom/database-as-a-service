# -*- coding: utf-8 -*-
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

    def get_resize_extra_steps(self):
        return (
            'workflow.steps.util.resize.agents.Start',
            'workflow.steps.util.database.CheckIsUp',
        )

    def get_resize_steps(self):
        return [{'Resizing database': (
            'workflow.steps.util.zabbix.DisableAlarms',
            'workflow.steps.util.vm.ChangeMaster',
            'workflow.steps.util.database.Stop',
            'workflow.steps.util.pack.ResizeConfigure',
            'workflow.steps.util.vm.Stop',
            'workflow.steps.util.vm.ChangeOffering',
            'workflow.steps.util.vm.Start',
            'workflow.steps.util.database.Start',
        ) + self.get_resize_extra_steps() + (
            'workflow.steps.util.infra.Offering',
            'workflow.steps.util.zabbix.EnableAlarms',
        )}]

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

    def get_upgrade_steps_description(self):
        return 'Disabling monitoring and alarms and upgrading database'

    def get_upgrade_steps_final_description(self):
        return 'Enabling monitoring and alarms'

    def get_upgrade_steps(self):
        return [{
            self.get_upgrade_steps_description(): (
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.zabbix.DestroyAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.CheckIsDown',
                'workflow.steps.util.vm.Stop',
                'workflow.steps.util.vm.InstallNewTemplate',
                'workflow.steps.util.vm.Start',
                'workflow.steps.util.vm.WaitingBeReady',
                'workflow.steps.util.vm.UpdateOSDescription',
            ) + self.get_upgrade_steps_extra() + (
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
            ),
        }] + self.get_upgrade_steps_final()

    def get_upgrade_steps_extra(self):
        return (
            'workflow.steps.util.plan.InitializationForUpgrade',
            'workflow.steps.util.plan.ConfigureForUpgrade',
            'workflow.steps.util.pack.Configure',
        )

    def get_upgrade_steps_final(self):
        return [{
            self.get_upgrade_steps_final_description(): (
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.CreateAlarmsForUpgrade',
            ),
        }]

    def get_add_database_instances_first_steps(self):
        raise NotImplementedError()

    def get_add_database_instances_last_steps(self):
        raise NotImplementedError()

    def get_add_database_instances_steps(self):
        return [{
            "Add instances":
            self.get_add_database_instances_first_steps() +
            (
            ) +
            self.get_add_database_instances_last_steps()
        }]

    def get_remove_readonly_instance_steps_first_steps(self):
        raise NotImplementedError()

    def get_remove_readonly_instance_steps_last_steps(self):
        raise NotImplementedError()

    def get_remove_readonly_instance_steps(self):
        return [{
            "Remove instance":
            self.get_remove_readonly_instance_steps_first_steps() +
            (
            ) +
            self.get_remove_readonly_instance_steps_last_steps()
        }]
