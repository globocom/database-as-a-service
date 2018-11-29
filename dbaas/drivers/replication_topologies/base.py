# -*- coding: utf-8 -*-
class BaseTopology(object):

    def deploy_instances(self):
        raise NotImplementedError

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

    def get_destroy_steps(self):
        return self.deploy_first_steps() + self.monitoring_steps() + self.deploy_last_steps()

    def get_clone_steps(self):
        raise NotImplementedError()

    def get_resize_extra_steps(self):
        return (
            'workflow.steps.util.database.Start',
            'workflow.steps.util.database.StartSlave',
            'workflow.steps.util.agents.Start',
            'workflow.steps.util.database.CheckIsUp',
            'workflow.steps.util.database.WaitForReplication',
        )

    def get_resize_steps(self):
        return [{'Resizing database': (
            'workflow.steps.util.zabbix.DisableAlarms',
            'workflow.steps.util.vm.ChangeMaster',
            'workflow.steps.util.database.CheckIfSwitchMaster',
            'workflow.steps.util.agents.Stop',
            'workflow.steps.util.database.StopSlave',
            'workflow.steps.util.database.Stop',
            'workflow.steps.util.plan.ResizeConfigure',
            'workflow.steps.util.host_provider.Stop',
            'workflow.steps.util.host_provider.ChangeOffering',
            'workflow.steps.util.host_provider.Start',
        ) + self.get_resize_extra_steps() + (
            'workflow.steps.util.infra.Offering',
            'workflow.steps.util.vm.InstanceIsSlave',
            'workflow.steps.util.zabbix.EnableAlarms',
        )}]

    def get_restore_snapshot_steps(self):
        raise NotImplementedError

    def get_upgrade_steps_initial_description(self):
        return 'Disable monitoring and alarms'

    def get_upgrade_steps_description(self):
        return 'Upgrading database'

    def get_upgrade_steps_final_description(self):
        return 'Enabling monitoring and alarms'

    def get_upgrade_steps(self):
        return [{
            self.get_upgrade_steps_initial_description(): (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
            ),
        }] + [{
            self.get_upgrade_steps_description(): (
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.CheckIfSwitchMaster',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.CheckIsDown',
                'workflow.steps.util.host_provider.Stop',
                'workflow.steps.util.host_provider.InstallNewTemplate',
                'workflow.steps.util.host_provider.Start',
                'workflow.steps.util.vm.WaitingBeReady',
                'workflow.steps.util.vm.UpdateOSDescription',
            ) + self.get_upgrade_steps_extra() + (
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.metric_collector.RestartTelegraf',
            ),
        }] + self.get_upgrade_steps_final()

    def get_upgrade_steps_extra(self):
        return (
            'workflow.steps.util.volume_provider.MountDataVolume',
            'workflow.steps.util.plan.InitializationForUpgrade',
            'workflow.steps.util.plan.ConfigureForUpgrade',
            'workflow.steps.util.metric_collector.ConfigureTelegraf',
        )

    def get_upgrade_steps_final(self):
        return [{
            self.get_upgrade_steps_final_description(): (
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
            ),
        }]

    def get_add_database_instances_first_steps(self):
        return (
            'workflow.steps.util.host_provider.CreateVirtualMachine',
            'workflow.steps.util.dns.CreateDNS',
            'workflow.steps.util.vm.WaitingBeReady',
            'workflow.steps.util.vm.UpdateOSDescription',
            'workflow.steps.util.volume_provider.NewVolume',
        )

    def get_add_database_instances_last_steps(self):
        return (
            'workflow.steps.util.acl.ReplicateAcls2NewInstance',
            'workflow.steps.util.acl.BindNewInstance',
            'workflow.steps.util.zabbix.CreateAlarms',
            'workflow.steps.util.db_monitor.CreateMonitoring',
        )

    def get_add_database_instances_middle_steps(self):
        return ()

    def get_add_database_instances_steps_description(self):
        return "Add instances"

    def get_remove_readonly_instance_steps_description(self):
        return "Remove instance"

    def get_add_database_instances_steps(self):
        return [{
            self.get_add_database_instances_steps_description():
            self.get_add_database_instances_first_steps() +
            self.get_add_database_instances_middle_steps() +
            self.get_add_database_instances_last_steps()
        }]

    def get_remove_readonly_instance_steps(self):
        return [{
            self.get_remove_readonly_instance_steps_description():
            self.get_add_database_instances_first_steps() +
            self.get_add_database_instances_middle_steps() +
            self.get_add_database_instances_last_steps()
        }]

    def get_change_parameter_steps_description(self):
        return 'Changing database parameters'

    def get_change_parameter_steps_final_description(self):
        return 'Setting parameter status'

    def get_change_parameter_steps_final(self):
        return [{
            self.get_change_parameter_steps_final_description(): (
                'workflow.steps.util.database.SetParameterStatus',
            ),
        }]

    def get_change_parameter_config_steps(self):
        return ('workflow.steps.util.plan.ConfigureOnlyDBConfigFile', )

    def get_change_static_parameter_steps(self):
        return [{
            self.get_change_parameter_steps_description(): (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.CheckIfSwitchMaster',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.CheckIsDown',
            ) + self.get_change_parameter_config_steps() + (
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
            )
        }] + self.get_change_parameter_steps_final()

    def get_change_dinamic_parameter_steps(self):
        return [{
            self.get_change_parameter_steps_description(): self.get_change_parameter_config_steps() +
            (
                'workflow.steps.util.database.ChangeDynamicParameters',
            )
        }] + self.get_change_parameter_steps_final()

    def get_change_dinamic_parameter_retry_steps_count(self):
        return 1

    def get_change_static_parameter_retry_steps_count(self):
        return 2

    def get_resize_oplog_steps(self):
        return ()

    def get_resize_oplog_steps_and_retry_steps_back(self):
        return self.get_resize_oplog_steps(), 0

    def get_switch_write_instance_steps_description(self):
        return "Switch write database instance"

    def get_switch_write_instance_steps(self):
        return [{
            self.get_switch_write_instance_steps_description():
            (
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.CheckIfSwitchMaster',
            )
        }]

    def get_reinstallvm_steps(self):
        return [{
            'Disable monitoring and alarms': (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
            ),
        }] + [{
            'Reinstall VM': (
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.CheckIfSwitchMaster',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.host_provider.Stop',
                'workflow.steps.util.host_provider.ReinstallTemplate',
                'workflow.steps.util.host_provider.Start',
                'workflow.steps.util.vm.WaitingBeReady',
                'workflow.steps.util.vm.UpdateOSDescription',
            ),
        }] + [{
            'Start Database': (
                'workflow.steps.util.volume_provider.MountDataVolume',
                'workflow.steps.util.plan.Initialization',
                'workflow.steps.util.plan.Configure',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.metric_collector.RestartTelegraf',
            ),
        }] + self.get_reinstallvm_steps_final()

    def get_reinstallvm_steps_final(self):
        return [{
            'Enabling monitoring and alarms': (
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
            ),
        }]

    def get_configure_ssl_steps(self):
        return [{
            'Disable monitoring and alarms': (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
            ),
        }] + [{
            'Configure SSL': (
                'workflow.steps.util.ssl.UpdateOpenSSlLib',
                'workflow.steps.util.ssl.CreateSSLFolder',
                'workflow.steps.util.ssl.CreateSSLConfForInfraEndPoint',
                'workflow.steps.util.ssl.RequestSSLForInfra',
                'workflow.steps.util.ssl.CreateJsonRequestFileInfra',
                'workflow.steps.util.ssl.CreateCertificateInfra',
                'workflow.steps.util.ssl.SetSSLFilesAccessMySQL',
                'workflow.steps.util.ssl.SetInfraConfiguredSSL',
                'workflow.steps.util.plan.Configure',
            ),
        }] + [{
            'Restart Database': (
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.Start',
            ),
        }] + [{
            'Enabling monitoring and alarms': (
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
            ),
        }]

    def get_host_migrate_steps(self):
        raise NotImplementedError

    def get_database_migrate_steps(self):
        raise NotImplementedError

    @property
    def driver_name(self):
        raise NotImplementedError


class FakeTestTopology(BaseTopology):

    @property
    def driver_name(self):
        return 'fake'


class InstanceDeploy():

    def __init__(self, instance_type , port):
        self.instance_type = instance_type
        self.port = port
