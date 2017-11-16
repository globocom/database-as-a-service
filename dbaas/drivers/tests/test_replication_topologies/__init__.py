# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from functools import wraps
from django.test import TestCase


def skip_unless_not_abstract(method):
    @wraps(method)
    def deco(*args, **kwargs):
        class_name = args[0].__class__.__name__
        if class_name.startswith('Abstract'):
            print("{!r} is abstract!".format(class_name))
            return lambda x, y: x
        return method(*args, **kwargs)
    return deco


class AbstractReplicationTopologySettingsTestCase(TestCase):

    def setUp(self):
        self.replication_topology = self._get_replication_topology_driver()

    def _get_replication_topology_driver(self):
        return None

    def _get_deploy_first_settings(self):
        raise NotImplementedError

    def _get_deploy_last_settings(self):
        raise NotImplementedError

    def _get_monitoring_settings(self):
        return (
            'workflow.steps.util.deploy.create_zabbix.CreateZabbix',
            'workflow.steps.util.deploy.create_dbmonitor.CreateDbMonitor',
        )

    def _get_deploy_settings(self):
        return self._get_deploy_first_settings() + \
               self._get_monitoring_settings() + \
               self._get_deploy_last_settings()

    def _get_clone_settings(self):
        raise NotImplementedError

    def _get_resize_extra_steps(self):
        return (
            'workflow.steps.util.database.StartSlave',
            'workflow.steps.util.agents.Start',
            'workflow.steps.util.database.CheckIsUp',
        )

    def _get_resize_settings(self):
        return [{'Resizing database': (
            'workflow.steps.util.zabbix.DisableAlarms',
            'workflow.steps.util.vm.ChangeMaster',
            'workflow.steps.util.agents.Stop',
            'workflow.steps.util.database.StopSlave',
            'workflow.steps.util.database.Stop',
            'workflow.steps.util.pack.ResizeConfigure',
            'workflow.steps.util.vm.Stop',
            'workflow.steps.util.vm.ChangeOffering',
            'workflow.steps.util.vm.Start',
            'workflow.steps.util.database.Start',
        ) + self._get_resize_extra_steps() + (
            'workflow.steps.util.infra.Offering',
            'workflow.steps.util.vm.InstanceIsSlave',
            'workflow.steps.util.zabbix.EnableAlarms',
        )}]

    def _get_restore_snapshot_settings(self):
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

    def _get_upgrade_steps_initial_description(self):
        return 'Disable monitoring and alarms'

    def _get_upgrade_steps_description(self):
        return 'Upgrading database'

    def _get_upgrade_steps_final_description(self):
        return 'Enabling monitoring and alarms'

    def _get_upgrade_settings(self):
        return [{
            self._get_upgrade_steps_initial_description(): (
                'workflow.steps.util.zabbix.DestroyAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
            )
        }] + [{
            self._get_upgrade_steps_description(): (
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.CheckIsDown',
                'workflow.steps.util.vm.Stop',
                'workflow.steps.util.vm.InstallNewTemplate',
                'workflow.steps.util.vm.Start',
                'workflow.steps.util.vm.WaitingBeReady',
                'workflow.steps.util.vm.UpdateOSDescription',
            ) + self._get_upgrade_steps_extra() + (
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
            ),
        }] + self._get_upgrade_steps_final()

    def _get_upgrade_steps_extra(self):
        return (
            'workflow.steps.util.plan.InitializationForUpgrade',
            'workflow.steps.util.plan.ConfigureForUpgrade',
            'workflow.steps.util.pack.Configure',
        )

    def _get_upgrade_steps_final(self):
        return [{
            self._get_upgrade_steps_final_description(): (
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.CreateAlarmsForUpgrade',
            ),
        }]

    def _get_add_database_instances_steps_description(self):
        return "Add instances"

    def _get_remove_readonly_instance_steps_description(self):
        return "Remove instance"

    def _get_add_database_instances_first_settings(self):
        return (
            'workflow.steps.util.vm.CreateVirtualMachineHorizontalElasticity',
            'workflow.steps.util.dns.CreateDNS',
            'workflow.steps.util.vm.WaitingBeReady',
            'workflow.steps.util.vm.UpdateOSDescription',
            'workflow.steps.util.disk.CreateExport',
        )

    def _get_add_database_instances_middle_settings(self):
        return ()

    def _get_add_database_instances_last_settings(self):
        return (
            'workflow.steps.util.acl.ReplicateAcls2NewInstance',
            'workflow.steps.util.acl.BindNewInstance',
            'workflow.steps.util.zabbix.CreateAlarms',
            'workflow.steps.util.db_monitor.CreateMonitoring',
        )

    def _get_add_database_instances_settings(self):
        return [{
            self._get_add_database_instances_steps_description():
            self._get_add_database_instances_first_settings() +
            self._get_add_database_instances_middle_settings() +
            self._get_add_database_instances_last_settings()
        }]

    def _get_remove_readonly_instance_settings(self):
        return [{
            self._get_remove_readonly_instance_steps_description():
                self._get_add_database_instances_first_settings() +
                self._get_add_database_instances_middle_settings() +
                self._get_add_database_instances_last_settings()
        }]

    def _get_change_parameter_steps_description(self):
        return 'Changing database parameters'

    def _get_change_parameter_steps_final_description(self):
        return 'Setting parameter status'

    def _get_change_parameter_steps_final(self):
        return [{
            self._get_change_parameter_steps_final_description(): (
                'workflow.steps.util.database.SetParameterStatus',
            ),
        }]

    def _get_change_parameter_config_steps(self):
        return ('workflow.steps.util.pack.Configure', )

    def _get_change_static_parameter_steps(self):
        return [{
            self._get_change_parameter_steps_description(): (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.CheckIsDown',
            ) + self._get_change_parameter_config_steps() + (
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
            )
        }] + self._get_change_parameter_steps_final()

    def _get_change_dinamic_parameter_steps(self):
        return [{
            self._get_change_parameter_steps_description(): self._get_change_parameter_config_steps() + (
                'workflow.steps.util.database.ChangeDynamicParameters',
            )
        }] + self._get_change_parameter_steps_final()

    def _get_resize_oplog_steps(self):
        return ()

    def _get_switch_write_instance_steps_description(self):
        return "Switch write database instance"

    def _get_switch_write_instance_steps(self):
        return [{
            self._get_switch_write_instance_steps_description():
            (
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.CheckIfSwitchMaster',
            )
        }]

    def _get_reinstallvm_steps(self):
        return [{
            'Disable monitoring and alarms': (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
            ),
        }] + [{
            'Reinstall VM': (
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.vm.Stop',
                'workflow.steps.util.vm.ReinstallTemplate',
                'workflow.steps.util.vm.Start',
                'workflow.steps.util.vm.WaitingBeReady',
                'workflow.steps.util.vm.UpdateOSDescription',
                'workflow.steps.util.plan.Initialization',
                'workflow.steps.util.plan.Configure',
                'workflow.steps.util.pack.Configure',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
            ),
        }] + self._get_reinstallvm_steps_final()

    def _get_reinstallvm_steps_final(self):
        return [{
            'Enabling monitoring and alarms': (
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
            ),
        }]

    @skip_unless_not_abstract
    def test_deploy_settings(self):
        self.assertEqual(
            self._get_deploy_settings(),
            self.replication_topology.get_deploy_steps()
        )

    @skip_unless_not_abstract
    def test_clone_settings(self):
        self.assertEqual(
            self._get_clone_settings(),
            self.replication_topology.get_clone_steps()
        )

    @skip_unless_not_abstract
    def test_resize_steps(self):
        self.assertEqual(
            self._get_resize_settings(),
            self.replication_topology.get_resize_steps()
        )

    @skip_unless_not_abstract
    def test_restore_snapshot_steps(self):
        self.assertEqual(
            self._get_restore_snapshot_settings(),
            self.replication_topology.get_restore_snapshot_steps()
        )

    @skip_unless_not_abstract
    def test_upgrade_steps(self):
        self.assertEqual(
            self._get_upgrade_settings(),
            self.replication_topology.get_upgrade_steps()
        )

    @skip_unless_not_abstract
    def test_add_database_instances_settings(self):
        self.assertEqual(
            self._get_add_database_instances_settings(),
            self.replication_topology.get_add_database_instances_steps()
        )

    @skip_unless_not_abstract
    def test_remove_readonly_instance_settings(self):
        self.assertEqual(
            self._get_remove_readonly_instance_settings(),
            self.replication_topology.get_remove_readonly_instance_steps()
        )

    @skip_unless_not_abstract
    def test_change_static_parameter_settings(self):
        self.assertEqual(
            self._get_change_static_parameter_steps(),
            self.replication_topology.get_change_static_parameter_steps()
        )

    @skip_unless_not_abstract
    def test_change_dinamic_parameter_settings(self):
        self.assertEqual(
            self._get_change_dinamic_parameter_steps(),
            self.replication_topology.get_change_dinamic_parameter_steps()
        )

    @skip_unless_not_abstract
    def test_resize_oplog_settings(self):
        self.assertEqual(
            self._get_resize_oplog_steps(),
            self.replication_topology.get_resize_oplog_steps()
        )

    @skip_unless_not_abstract
    def test_switch_write_instance_settings(self):
        self.assertEqual(
            self._get_switch_write_instance_steps(),
            self.replication_topology.get_switch_write_instance_steps()
        )

    @skip_unless_not_abstract
    def test_reinstallvm_settings(self):
        self.assertEqual(
            self._get_reinstallvm_steps(),
            self.replication_topology.get_reinstallvm_steps()
        )
