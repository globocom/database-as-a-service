# -*- coding: utf-8 -*-
import logging
from util import get_credentials_for
from dbaas_credentials.models import CredentialType
from dbaas_foxha.provider import FoxHAProvider
from dbaas_foxha.dbaas_api import DatabaseAsAServiceApi
from base import BaseTopology, InstanceDeploy
from physical.models import Instance

LOG = logging.getLogger(__name__)


class BaseMysql(BaseTopology):
    def deploy_first_steps(self):
        return (
            'workflow.steps.util.deploy.build_databaseinfra.BuildDatabaseInfra',
            'workflow.steps.mysql.deploy.create_virtualmachines.CreateVirtualMachine',
            'workflow.steps.mysql.deploy.create_secondary_ip.CreateSecondaryIp',
            'workflow.steps.mysql.deploy.create_dns.CreateDns',
            'workflow.steps.util.deploy.create_nfs.CreateNfs',
            'workflow.steps.mysql.deploy.init_database.InitDatabase',
            'workflow.steps.util.deploy.check_database_connection.CheckDatabaseConnection',
            'workflow.steps.util.deploy.check_dns.CheckDns',
            'workflow.steps.util.deploy.start_monit.StartMonit',
        )

    def get_resize_extra_steps(self):
        return (
            'workflow.steps.util.database.CheckIsUp',
            'workflow.steps.util.database.StartSlave',
            'workflow.steps.util.agents.Start',
            'workflow.steps.util.database.WaitForReplication',
        )

    def deploy_last_steps(self):
        return (
            'workflow.steps.util.deploy.build_database.BuildDatabase',
            'workflow.steps.util.deploy.check_database_binds.CheckDatabaseBinds',
        )

    def get_clone_steps(self):
        return self.deploy_first_steps() + self.deploy_last_steps() + (
            'workflow.steps.util.clone.clone_database.CloneDatabase',
        ) + self.monitoring_steps()

    def switch_master(self, driver):
        raise NotImplementedError()

    def check_instance_is_master(self, driver, instance):
        raise NotImplementedError

    def set_master(self, driver, instance):
        raise NotImplementedError

    def set_read_ip(self, driver, instance):
        raise NotImplementedError

    def get_database_agents(self):
        return ['monit']


class MySQLSingle(BaseMysql):

    def get_deploy_steps(self):
        return [{
            'Creating virtual machine': (
                'workflow.steps.util.host_provider.CreateVirtualMachine',
            )}, {
            'Creating dns': (
                'workflow.steps.util.dns.CreateDNS',
            )}, {
            'Creating disk': (
                'workflow.steps.util.volume_provider.NewVolume',
            )}, {
            'Waiting VMs': (
                'workflow.steps.util.vm.WaitingBeReady',
                'workflow.steps.util.vm.UpdateOSDescription'
            )}, {
            'Check DNS': (
                'workflow.steps.util.dns.CheckIsReady',
            )}, {
            'Configuring database': (
                'workflow.steps.util.volume_provider.MountDataVolume',
                'workflow.steps.util.infra.UpdateEndpoint',
                'workflow.steps.util.plan.InitializationForNewInfra',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
            )}, {
            'Configure SSL': (
                'workflow.steps.util.ssl.UpdateOpenSSlLib',
                'workflow.steps.util.ssl.CreateSSLFolder',
                'workflow.steps.util.ssl.CreateSSLConfForInfraEndPoint',
                'workflow.steps.util.ssl.RequestSSLForInfra',
                'workflow.steps.util.ssl.CreateJsonRequestFileInfra',
                'workflow.steps.util.ssl.CreateCertificateInfra',
                'workflow.steps.util.ssl.SetSSLFilesAccessMySQL',
                'workflow.steps.util.ssl.SetInfraConfiguredSSL',
            )}, {
            'Starting database': (
                'workflow.steps.util.plan.ConfigureForNewInfra',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.metric_collector.RestartTelegraf',
                'workflow.steps.util.database.StartMonit',
            )}, {
            'Creating Database': (
                'workflow.steps.util.database.Create',
            )}, {
            'Check ACL': (
                'workflow.steps.util.acl.BindNewInstance',
            )}, {
            'Creating monitoring and alarms': (
                'workflow.steps.util.zabbix.CreateAlarms',
                'workflow.steps.util.db_monitor.CreateInfraMonitoring',
            )
        }]

    def switch_master(self, driver):
        return True

    def check_instance_is_master(self, driver, instance):
        return True

    def set_master(self, driver, instance):
        raise True

    def set_read_ip(self, driver, instance):
        raise True

    @property
    def driver_name(self):
        return 'mysql_single'

    def deploy_instances(self):
        return [[InstanceDeploy(Instance.MYSQL, 3306)]]

    def get_restore_snapshot_steps(self):
        return [{
            'Disable monitoring': (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
            )}, {
            'Restoring': (
                'workflow.steps.util.volume_provider.RestoreSnapshot',
            )}, {
            'Stopping datbase': (
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.CheckIsDown',
            )}, {
            'Configuring': (
                'workflow.steps.util.volume_provider.AddAccessRestoredVolume',
                'workflow.steps.util.volume_provider.UnmountActiveVolume',
                'workflow.steps.util.volume_provider.MountDataVolumeRestored',
                'workflow.steps.util.plan.ConfigureRestore',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
            )}, {
            'Starting database': (
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.metric_collector.RestartTelegraf',
            )}, {
            'Old data': (
                'workflow.steps.util.volume_provider.TakeSnapshot',
                'workflow.steps.util.volume_provider.UpdateActiveDisk',
            )}, {
            'Enabling monitoring': (
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
            )
        }]


class MySQLFoxHA(MySQLSingle):

    def deploy_first_steps(self):
        return (
            'workflow.steps.util.deploy.build_databaseinfra.BuildDatabaseInfra',
            'workflow.steps.mysql.deploy.create_virtualmachines_fox.CreateVirtualMachine',
            'workflow.steps.mysql.deploy.create_vip.CreateVip',
            'workflow.steps.mysql.deploy.create_dns_foxha.CreateDnsFoxHA',
            'workflow.steps.util.deploy.create_nfs.CreateNfs',
            'workflow.steps.mysql.deploy.init_database_foxha.InitDatabaseFoxHA',
            'workflow.steps.mysql.deploy.check_pupet.CheckVMName',
            'workflow.steps.mysql.deploy.check_pupet.CheckPuppetIsRunning',
            'workflow.steps.mysql.deploy.config_vms_foreman.ConfigVMsForeman',
            'workflow.steps.mysql.deploy.run_pupet_setup.RunPuppetSetup',
            'workflow.steps.mysql.deploy.config_fox.ConfigFox',
            'workflow.steps.mysql.deploy.check_replication.CheckReplicationFoxHA',
            'workflow.steps.util.deploy.check_database_connection.CheckDatabaseConnection',
            'workflow.steps.util.deploy.check_dns.CheckDns',
            'workflow.steps.util.deploy.start_monit.StartMonit',
        )

    def deploy_last_steps(self):
        return (
            'workflow.steps.util.deploy.build_database.BuildDatabase',
            'workflow.steps.util.deploy.check_database_binds.CheckDatabaseBinds',
        )

    def _get_fox_provider(self, driver):
        databaseinfra = driver.databaseinfra

        foxha_credentials = get_credentials_for(
            environment=databaseinfra.environment,
            credential_type=CredentialType.FOXHA
        )
        dbaas_api = DatabaseAsAServiceApi(databaseinfra, foxha_credentials)
        return FoxHAProvider(dbaas_api)

    def switch_master(self, driver):
        self._get_fox_provider(driver).switchover(
            group_name=driver.databaseinfra.name
        )

    def check_instance_is_master(self, driver, instance):
        fox_node_is_master = self._get_fox_provider(driver).node_is_master(
            group_name=driver.databaseinfra.name,
            node_ip=instance.address
        )

        if not fox_node_is_master:
            return fox_node_is_master

        query = "show variables like 'server_id'"

        try:
            instance_result = driver.query(query, instance)
            master_result = driver.query(query)
        except Exception, e:
            LOG.warning("Ops... %s" % e)
            return False

        instance_server_id = int(instance_result[0]['Value'])
        master_server_id = int(master_result[0]['Value'])

        return instance_server_id == master_server_id

    def set_master(self, driver, instance):
        self._get_fox_provider(driver).set_master(
            group_name=driver.databaseinfra.name,
            node_ip=instance.address
        )

    def set_read_ip(self, driver, instance):
        self._get_fox_provider(driver).set_read_only(
            group_name=driver.databaseinfra.name,
            node_ip=instance.address
        )

    def get_database_agents(self):
        agents = ['httpd', '/etc/init.d/pt-heartbeat']
        return super(MySQLFoxHA, self).get_database_agents() + agents

    def add_database_instances_first_steps(self):
        return ()

    def add_database_instances_last_steps(self):
        return ()

    @property
    def driver_name(self):
        return 'mysql_foxha'

    def deploy_instances(self):
        return [
            [InstanceDeploy(Instance.MYSQL, 3306)],
            [InstanceDeploy(Instance.MYSQL, 3306)]
        ]

    def get_deploy_steps(self):
        return [{
            'Creating virtual machine': (
                'workflow.steps.util.host_provider.CreateVirtualMachine',
            )}, {
            'Creating VIP': (
                'workflow.steps.util.network.CreateVip',
                'workflow.steps.util.dns.RegisterDNSVip',
            )}, {
            'Creating dns': (
                'workflow.steps.util.dns.CreateDNS',
            )}, {
            'Creating disk': (
                'workflow.steps.util.volume_provider.NewVolume',
            )}, {
            'Waiting VMs': (
                'workflow.steps.util.vm.WaitingBeReady',
                'workflow.steps.util.vm.UpdateOSDescription',
                'workflow.steps.util.vm.CheckHostNameAndReboot',
            )}, {
            'Check hostname': (
                'workflow.steps.util.vm.WaitingBeReady',
                'workflow.steps.util.vm.CheckHostName',
            )}, {
            'Check puppet': (
                'workflow.steps.util.puppet.WaitingBeStarted',
                'workflow.steps.util.puppet.WaitingBeDone',
                'workflow.steps.util.puppet.ExecuteIfProblem',
                'workflow.steps.util.puppet.WaitingBeDone',
                'workflow.steps.util.puppet.CheckStatus',
            )}, {
            'Configure foreman': (
                'workflow.steps.util.foreman.SetupDSRC',
            )}, {
            'Running puppet': (
                'workflow.steps.util.puppet.Execute',
                'workflow.steps.util.puppet.CheckStatus',
            )}, {
            'Check DNS': (
                'workflow.steps.util.dns.CheckIsReady',
            )}, {
            'Configuring database': (
                'workflow.steps.util.volume_provider.MountDataVolume',
                'workflow.steps.util.plan.InitializationForNewInfra',
            )}, {
            'Configure SSL': (
                'workflow.steps.util.ssl.UpdateOpenSSlLib',
                'workflow.steps.util.ssl.CreateSSLFolder',
                'workflow.steps.util.ssl.CreateSSLConfForInfraEndPoint',
                'workflow.steps.util.ssl.CreateSSLConfForInstanceIP',
                'workflow.steps.util.ssl.RequestSSLForInfra',
                'workflow.steps.util.ssl.RequestSSLForInstance',
                'workflow.steps.util.ssl.CreateJsonRequestFileInfra',
                'workflow.steps.util.ssl.CreateJsonRequestFileInstance',
                'workflow.steps.util.ssl.CreateCertificateInfra',
                'workflow.steps.util.ssl.CreateCertificateInstance',
                'workflow.steps.util.ssl.SetSSLFilesAccessMySQL',
                'workflow.steps.util.ssl.SetInfraConfiguredSSL',
            )}, {
            'Starting database': (
                'workflow.steps.util.plan.ConfigureForNewInfra',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.metric_collector.RestartTelegraf',
            )}, {
            'Check database': (
                'workflow.steps.util.plan.StartReplicationNewInfra',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.database.StartMonit',
            )}, {
            'FoxHA configure': (
                'workflow.steps.util.fox.ConfigureGroup',
                'workflow.steps.util.fox.ConfigureNode',
            )}, {
            'FoxHA start': (
                'workflow.steps.util.fox.Start',
                'workflow.steps.util.fox.IsReplicationOk'
            )}, {
            'Configure Replication User': (
                'workflow.steps.util.ssl.SetReplicationUserRequireSSL',
            )}, {
            'Creating Database': (
                'workflow.steps.util.database.Create',
            )}, {
            'Check ACL': (
                'workflow.steps.util.acl.BindNewInstance',
            )}, {
            'Creating monitoring and alarms': (
                'workflow.steps.util.mysql.CreateAlarmsVip',
                'workflow.steps.util.zabbix.CreateAlarms',
                'workflow.steps.util.db_monitor.CreateInfraMonitoring',
            )
        }]

    def get_restore_snapshot_steps(self):
        return [{
            'Disable monitoring': (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
            )}, {
            'Restoring': (
                'workflow.steps.util.mysql.RestoreSnapshotMySQL',
            )}, {
            'Stopping datbase': (
                'workflow.steps.util.mysql.SaveMySQLBinlog',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.CheckIsDown',
            )}, {
            'Configuring': (
                'workflow.steps.util.mysql.AddDiskPermissionsRestoredDiskMySQL',
                'workflow.steps.util.mysql.UnmountOldestExportRestoreMySQL',
                'workflow.steps.util.mysql.MountNewerExportRestoreMySQL',
                'workflow.steps.util.disk.RemoveDeprecatedFiles',
                'workflow.steps.util.plan.ConfigureRestore',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
            )}, {
            'Starting database': (
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.metric_collector.RestartTelegraf',
            )}, {
            'Configuring replication': (
                'workflow.steps.util.mysql.SetMasterRestore',
            )}, {
            'Start slave': (
                'workflow.steps.util.mysql.StartSlave',
            )}, {
            'Configure FoxHA': (
                'workflow.steps.util.mysql.ConfigureFoxHARestore',
            )}, {
            'Check database': (
                'workflow.steps.util.database.CheckIsUp',
            )}, {
            'Old data': (
                'workflow.steps.util.volume_provider.TakeSnapshot',
                'workflow.steps.util.volume_provider.UpdateActiveDisk',
            )}, {
            'Enabling monitoring': (
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
            )
        }]

    def get_upgrade_steps_extra(self):
        return super(MySQLFoxHA, self).get_upgrade_steps_extra() + (
            'workflow.steps.util.vm.CheckHostName',
            'workflow.steps.util.puppet.WaitingBeStarted',
            'workflow.steps.util.puppet.WaitingBeDone',
            'workflow.steps.util.puppet.ExecuteIfProblem',
            'workflow.steps.util.puppet.WaitingBeDone',
            'workflow.steps.util.puppet.CheckStatus',
            'workflow.steps.util.foreman.SetupDSRC',
            'workflow.steps.util.puppet.Execute',
            'workflow.steps.util.puppet.CheckStatus',
        )

    def get_reinstallvm_steps(self):
        return [{
            'Disable monitoring and alarms': (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
            ),
        }] + [{
            'Reinstall VM': (
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.foreman.DeleteHost',
                'workflow.steps.util.host_provider.Stop',
                'workflow.steps.util.host_provider.ReinstallTemplate',
                'workflow.steps.util.host_provider.Start',
                'workflow.steps.util.vm.WaitingBeReady',
                'workflow.steps.util.vm.UpdateOSDescription',
            ),
        }] + [{
            'Configure Puppet': (
                'workflow.steps.util.vm.CheckHostName',
                'workflow.steps.util.puppet.WaitingBeStarted',
                'workflow.steps.util.puppet.WaitingBeDone',
                'workflow.steps.util.puppet.ExecuteIfProblem',
                'workflow.steps.util.puppet.WaitingBeDone',
                'workflow.steps.util.puppet.CheckStatus',
                'workflow.steps.util.foreman.SetupDSRC',
                'workflow.steps.util.puppet.Execute',
                'workflow.steps.util.puppet.CheckStatus',
            ),
        }] + [{
            'Start Database': (
                'workflow.steps.util.volume_provider.MountDataVolume',
                'workflow.steps.util.plan.Initialization',
                'workflow.steps.util.plan.Configure',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.metric_collector.RestartTelegraf',
            ),
        }] + self.get_reinstallvm_steps_final()

    def get_upgrade_steps(self):
        return [{
            self.get_upgrade_steps_initial_description(): (
                'workflow.steps.util.zabbix.DestroyAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
            ),
        }] + [{
            self.get_upgrade_steps_description(): (
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.CheckIsDown',
                'workflow.steps.util.foreman.DeleteHost',
                'workflow.steps.util.host_provider.Stop',
                'workflow.steps.util.host_provider.InstallNewTemplate',
                'workflow.steps.util.host_provider.Start',
                'workflow.steps.util.vm.WaitingBeReady',
                'workflow.steps.util.vm.UpdateOSDescription',
            ) + self.get_upgrade_steps_extra() + (
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
            ),
        }] + self.get_upgrade_steps_final()

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
                'workflow.steps.util.ssl.CreateSSLConfForInstanceIP',
                'workflow.steps.util.ssl.RequestSSLForInfra',
                'workflow.steps.util.ssl.RequestSSLForInstance',
                'workflow.steps.util.ssl.CreateJsonRequestFileInfra',
                'workflow.steps.util.ssl.CreateJsonRequestFileInstance',
                'workflow.steps.util.ssl.CreateCertificateInfra',
                'workflow.steps.util.ssl.CreateCertificateInstance',
                'workflow.steps.util.ssl.SetSSLFilesAccessMySQL',
                'workflow.steps.util.ssl.SetInfraConfiguredSSL',
                'workflow.steps.util.plan.Configure',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
            ),
        }] + [{
            'Restart Database': (
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.CheckIfSwitchMaster',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.metric_collector.RestartTelegraf',
            ),
        }] + [{
            'Configure Replication User': (
                'workflow.steps.util.ssl.SetReplicationUserRequireSSL',
            ),
        }] + [{
            'Enabling monitoring and alarms': (
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
            ),
        }]