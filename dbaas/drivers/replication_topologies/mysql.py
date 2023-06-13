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
    def get_resize_extra_steps(self):
        return (
            'workflow.steps.util.database.CheckIsUp',
            'workflow.steps.util.database.StartSlave',
            'workflow.steps.util.agents.Start',
            'workflow.steps.util.database.WaitForReplication',
        )

    def switch_master(self, driver):
        raise NotImplementedError()

    def check_instance_is_master(self, driver, instance,
                                 default_timeout=False):
        raise NotImplementedError

    def set_master(self, driver, instance):
        raise NotImplementedError

    def set_read_ip(self, driver, instance):
        raise NotImplementedError

    def get_database_agents(self):
        return ['monit']

    def get_change_binaries_upgrade_patch_steps(self):
        return (
            'workflow.steps.util.database_upgrade_patch.MySQLCHGBinStep',
        )

    def get_change_binaries_upgrade_patch_steps_rollback(self):
        return (
            ('workflow.steps.util.database_upgrade_patch'
             '.MySQLCHGBinStepRollback'),
        )

    def get_configure_ssl_libs_and_folder_steps(self):
        return (
            'workflow.steps.util.ssl.UpdateOpenSSlLibIfConfigured',
            'workflow.steps.util.ssl.CreateSSLFolderIfConfigured',
        )

    def get_configure_ssl_ip_steps(self):
        return ()

    def get_configure_ssl_dns_steps(self):
        return (
            'workflow.steps.util.ssl.CreateSSLConfForInfraEndPointIfConfigured',
            'workflow.steps.util.ssl.RequestSSLForInfraIfConfigured',
            'workflow.steps.util.ssl.CreateJsonRequestFileInfraIfConfigured',
            'workflow.steps.util.ssl.CreateCertificateInfraIfConfigured',
            'workflow.steps.util.ssl.SetSSLFilesAccessMySQLIfConfigured',
            'workflow.steps.util.ssl.UpdateExpireAtDate',
        )


class MySQLSingle(BaseMysql):

    def get_clone_steps(self):
        return [{
            'Creating Service Account': (
                'workflow.steps.util.host_provider.CreateServiceAccount',
                'workflow.steps.util.host_provider.SetServiceAccountRoles'
            )}, {
            'Creating virtual machine': (
                'workflow.steps.util.host_provider.AllocateIP',
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
                'workflow.steps.util.volume_provider.AttachDataVolume',
                'workflow.steps.util.volume_provider.MountDataVolume',
                'workflow.steps.util.infra.UpdateEndpoint',
                'workflow.steps.util.plan.InitializationForNewInfra',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
            )}, {
            'Configure SSL': (
                'workflow.steps.util.ssl.UpdateOpenSSlLib',
                'workflow.steps.util.ssl.CreateSSLFolderRollbackIfRunning',
                'workflow.steps.util.ssl.CreateSSLConfForInfraEndPoint',
                'workflow.steps.util.ssl.RequestSSLForInfra',
                'workflow.steps.util.ssl.CreateJsonRequestFileInfra',
                'workflow.steps.util.ssl.CreateCertificateInfra',
                'workflow.steps.util.ssl.SetSSLFilesAccessMySQL',
                'workflow.steps.util.ssl.SetInfraConfiguredSSL',
                'workflow.steps.util.ssl.UpdateExpireAtDate',
            )}, {
            'Starting database': (
                'workflow.steps.util.plan.ConfigureForNewInfra',
                'workflow.steps.util.plan.ConfigureLogForNewInfra',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.metric_collector.RestartTelegraf',
                'workflow.steps.util.database.StartRsyslog',
                'workflow.steps.util.database.StartMonit',
            )}, {
            'Creating Database': (
                'workflow.steps.util.database.Clone',
                'workflow.steps.util.clone.clone_database.CloneDatabaseData'
            )}, {
            'Check ACL': (
                'workflow.steps.util.acl.BindNewInstance',
            )}, {
            'Creating monitoring and alarms': (
                'workflow.steps.util.zabbix.CreateAlarms',
                'workflow.steps.util.db_monitor.CreateInfraMonitoring',
            )}, {
            'Create Extra DNS': (
                'workflow.steps.util.database.CreateExtraDNS',
            )}, {
            'Update Host Disk Size': (
                'workflow.steps.util.host_provider.UpdateHostRootVolumeSize',
            )
        }]

    def get_deploy_steps(self):
        return [{
            'Creating Service Account': (
                'workflow.steps.util.host_provider.CreateServiceAccount',
                'workflow.steps.util.host_provider.SetServiceAccountRoles'
            )}, {
            'Creating virtual machine': (
                'workflow.steps.util.host_provider.AllocateIP',
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
                'workflow.steps.util.volume_provider.AttachDataVolumeWithUndo',
                'workflow.steps.util.volume_provider.MountDataVolume',
                'workflow.steps.util.infra.UpdateEndpoint',
                'workflow.steps.util.plan.InitializationForNewInfra',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
            )}, {
            'Configure SSL': (
                'workflow.steps.util.ssl.UpdateOpenSSlLib',
                'workflow.steps.util.ssl.CreateSSLFolderRollbackIfRunning',
                'workflow.steps.util.ssl.CreateSSLConfForInfraEndPoint',
                'workflow.steps.util.ssl.RequestSSLForInfra',
                'workflow.steps.util.ssl.CreateJsonRequestFileInfra',
                'workflow.steps.util.ssl.CreateCertificateInfra',
                'workflow.steps.util.ssl.SetSSLFilesAccessMySQL',
                'workflow.steps.util.ssl.SetInfraConfiguredSSL',
                'workflow.steps.util.ssl.UpdateExpireAtDate',
            )}, {
            'Starting database': (
                'workflow.steps.util.plan.ConfigureForNewInfra',
                'workflow.steps.util.plan.ConfigureLogForNewInfra',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.metric_collector.RestartTelegraf',
                'workflow.steps.util.database.StartMonit',
                'workflow.steps.util.database.StartRsyslog',
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
                'workflow.steps.util.database.ConfigurePrometheusMonitoring'
            )}, {
            'Create Extra DNS': (
                'workflow.steps.util.database.CreateExtraDNS',
            )}, {
            'Update Host Disk Size': (
                'workflow.steps.util.host_provider.UpdateHostRootVolumeSize',
            ),
            'Save Snapshot': (
                'workflow.steps.util.database.MakeSnapshot',
            )
        }] + self.get_configure_db_params_steps()
    
    def get_configure_db_params_steps(self):
        return [{
            'Configuring DB Params': (
                'workflow.steps.util.database.CreateParameterChange',
                'workflow.steps.util.plan.ConfigureOnlyDBConfigFile',
                'workflow.steps.util.database.ChangeDynamicParameters',
                'workflow.steps.util.database.UpdateKernelParameters',
            )}] + self.get_change_parameter_steps_final()

    def get_configure_static_db_params_steps(self):
        return [{
            'Configuring Static DB Params': (
                'workflow.steps.util.database.CreateStaticParameterChange',
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
                'workflow.steps.util.database.checkAndFixMySQLReplication',
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.CheckIfSwitchMaster',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.CheckIsDown',
                'workflow.steps.util.plan.ConfigureOnlyDBConfigFile',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
            )
        }] + self.get_change_parameter_steps_final()

    def get_host_migrate_steps(self):
        return [{
            'Migrating': (
                ('workflow.steps.util.host_provider'
                 '.CreateVirtualMachineMigrate'),
                'workflow.steps.util.vm.WaitingBeReady',
                'workflow.steps.util.vm.UpdateOSDescription',
                'workflow.steps.util.host_provider.UpdateHostRootVolumeSize',
                'workflow.steps.util.volume_provider.NewVolume',
                'workflow.steps.util.volume_provider.AttachDataVolume',
                'workflow.steps.util.volume_provider.MountDataVolume',
                'workflow.steps.util.volume_provider.TakeSnapshotMigrate',
                ('workflow.steps.util.volume_provider'
                 '.WaitSnapshotAvailableMigrate'),
                'workflow.steps.util.volume_provider.AddAccessMigrate',
                'workflow.steps.util.volume_provider.MountDataVolumeMigrate',
                'workflow.steps.util.volume_provider.CopyFilesMigrate',
                'workflow.steps.util.volume_provider.DetachDataVolumeMigrate',
                'workflow.steps.util.volume_provider.UmountDataVolumeMigrate',
                'workflow.steps.util.volume_provider.RemoveAccessMigrate',
                'workflow.steps.util.volume_provider.RemoveSnapshotMigrate',
                'workflow.steps.util.disk.RemoveDeprecatedFiles',
                'workflow.steps.util.plan.ConfigureForNewInfra',
                'workflow.steps.util.plan.ConfigureLogForNewInfra',
                'workflow.steps.util.mysql.SetFilePermission',
                ) + self.get_change_binaries_upgrade_patch_steps() + (
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.acl.ReplicateAclsMigrate',
                'workflow.steps.util.zabbix.DestroyAlarms',
                'workflow.steps.util.dns.ChangeEndpoint',
                'workflow.steps.util.dns.CheckIsReady',
                'workflow.steps.util.ssl.UpdateOpenSSlLibIfConfigured',
                'workflow.steps.util.ssl.CreateSSLFolderIfConfigured',
                ('workflow.steps.util.ssl'
                 '.CreateSSLConfForInfraEndPointIfConfigured'),
                'workflow.steps.util.ssl.RequestSSLForInfraIfConfigured',
                ('workflow.steps.util.ssl'
                 '.CreateJsonRequestFileInfraIfConfigured'),
                'workflow.steps.util.ssl.CreateCertificateInfraIfConfigured',
                'workflow.steps.util.ssl.SetSSLFilesAccessMySQLIfConfigured',
                'workflow.steps.util.ssl.UpdateExpireAtDate',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
                'workflow.steps.util.metric_collector.RestartTelegraf',
                'workflow.steps.util.zabbix.CreateAlarms',
                'workflow.steps.util.disk.ChangeSnapshotOwner',
                'workflow.steps.util.volume_provider.DestroyOldEnvironment',
                ('workflow.steps.util.host_provider'
                 '.DestroyVirtualMachineMigrate'),
            )
        }]

    def get_update_ssl_steps(self):
        return [{
            'Disable monitoring and alarms': (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
                'workflow.steps.util.ssl.UpdateExpireAtDateRollback',
                'workflow.steps.util.ssl.BackupSSLFolder',
            ),
        }] + [{
            'Configure SSL': (
                'workflow.steps.util.ssl.UpdateSSLForInfra',
                'workflow.steps.util.ssl.CreateJsonRequestFileInfra',
                'workflow.steps.util.ssl.CreateCertificateInfra',
                'workflow.steps.util.ssl.SetSSLFilesAccessMySQL',
                'workflow.steps.util.ssl.UpdateExpireAtDate',
            ),
        }] + [{
            'Restart Database': (
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.ssl.RestoreSSLFolder4Rollback',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.metric_collector.RestartTelegraf',
            ),
        }] + [{
            'Enabling monitoring and alarms': (
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
            ),
        }]

    def switch_master(self, driver):
        return True

    def check_instance_is_master(self, driver, instance, default_timeout=False):
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
            'Stopping database': (
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.StopRsyslog',
                'workflow.steps.util.database.CheckIsDown',
            )}, {
            'Configuring': (
                'workflow.steps.util.volume_provider.AddAccessRestoredVolume',
                'workflow.steps.util.volume_provider.UnmountActiveVolume',
                'workflow.steps.util.volume_provider.AttachDataVolumeRestored',
                'workflow.steps.util.volume_provider.MountDataVolumeRestored',
                'workflow.steps.util.plan.ConfigureRestore',
                'workflow.steps.util.plan.ConfigureLog',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
            )}, {
            'Configure SSL': (
                'workflow.steps.util.disk.CleanSSLDir',
                ('workflow.steps.util.ssl'
                 '.CreateSSLConfForInfraEndPointIfConfigured'),
                'workflow.steps.util.ssl.RequestSSLForInfraIfConfigured',
                ('workflow.steps.util.ssl'
                 '.CreateJsonRequestFileInfraIfConfigured'),
                'workflow.steps.util.ssl.CreateCertificateInfraIfConfigured',
                'workflow.steps.util.ssl.SetSSLFilesAccessMySQLIfConfigured',
                'workflow.steps.util.ssl.UpdateExpireAtDate',
            )}, {
            'Starting database': (
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.StartRsyslog',
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

    def get_filer_migrate_steps(self):
        return [{
            'Migrating': (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
                'workflow.steps.util.volume_provider.NewInactiveVolume',
                'workflow.steps.util.metric_collector.StopTelegraf',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.StopRsyslog',
                'workflow.steps.util.database.CheckIsDown',
                'workflow.steps.util.volume_provider.AddAccessNewVolume',
                'workflow.steps.util.volume_provider.MountDataLatestVolume',
                'workflow.steps.util.volume_provider.CopyFiles',
                'workflow.steps.util.volume_provider.UnmountDataLatestVolume',
                'workflow.steps.util.volume_provider.DetachDataVolume',
                'workflow.steps.util.volume_provider.UnmountDataVolume',
                'workflow.steps.util.volume_provider.MountDataNewVolume',
                'workflow.steps.util.mysql.SetFilePermission',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.StartRsyslog',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.metric_collector.RestartTelegraf',
                'workflow.steps.util.volume_provider.TakeSnapshotOldDisk',
                'workflow.steps.util.volume_provider.UpdateActiveDisk',
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
            )}
        ]

    def get_upgrade_steps_extra(self):
        return super(MySQLSingle, self).get_upgrade_steps_extra() + (
            'workflow.steps.util.mysql.SetFilePermission',
            'workflow.steps.util.plan.Configure',
            'workflow.steps.util.plan.ConfigureLog',
            'workflow.steps.util.database.Start',
            'workflow.steps.util.database.CheckIsUp',
            'workflow.steps.util.mysql.RunMySQLUpgrade',
            'workflow.steps.util.mysql.InstallAuditPlugin',
            'workflow.steps.util.mysql.CheckIfAuditPluginIsInstalled',
            'workflow.steps.util.database.Stop',
            'workflow.steps.util.plan.ConfigureForUpgrade',
            'workflow.steps.util.plan.ConfigureLog',
        )


class MySQLFoxHA(MySQLSingle):
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

    def check_instance_is_master(self, driver, instance, default_timeout=False):
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
        except Exception as e:
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
        agents = ['httpd', 'pt-heartbeat']
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
            'Creating Service Account': (
                'workflow.steps.util.host_provider.CreateServiceAccount',
                'workflow.steps.util.host_provider.SetServiceAccountRoles'
            )}, {
            'Creating virtual machine': (
                'workflow.steps.util.host_provider.AllocateIP',
                'workflow.steps.util.host_provider.CreateVirtualMachine',
            )}, {
            'Creating VIP': (
                'workflow.steps.util.vip_provider.CreateVip',
                'workflow.steps.util.vip_provider.CreateInstanceGroup',
                'workflow.steps.util.vip_provider.AddInstancesInGroup',
                'workflow.steps.util.vip_provider.CreateHeathcheck',
                'workflow.steps.util.vip_provider.CreateBackendService',
                'workflow.steps.util.vip_provider.AllocateIP',
                'workflow.steps.util.vip_provider.AllocateDNS',
                'workflow.steps.util.vip_provider.CreateForwardingRule',
                'workflow.steps.util.vip_provider.AddLoadBalanceLabels',
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
                'workflow.steps.util.volume_provider.AttachDataVolumeWithUndo',
                'workflow.steps.util.volume_provider.MountDataVolume',
                'workflow.steps.util.plan.InitializationForNewInfra',
            )}, {
            'Configure SSL': (
                'workflow.steps.util.ssl.UpdateOpenSSlLib',
                'workflow.steps.util.ssl.CreateSSLFolderRollbackIfRunning',
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
                'workflow.steps.util.ssl.UpdateExpireAtDate',
            )}, {
            'Starting database': (
                'workflow.steps.util.plan.ConfigureForNewInfra', # mysql_foxha_57_configuration.sh
                'workflow.steps.util.plan.ConfigureLogForNewInfra', # rsyslog_config.sh
                'workflow.steps.util.metric_collector.ConfigureTelegraf', # desativar? não tem mais o sofia...
                'workflow.steps.util.database.Start', # start database
                'workflow.steps.util.metric_collector.RestartTelegraf', # desativar? não tem mais o sofia...
                'workflow.steps.util.database.StartRsyslog', # start rsyslog. `sudo systemctl start rsyslog.service` e no ol6 era `/etc/init.d/rsyslog start`
                'workflow.steps.util.database.CheckIsUp', #checa se o is_up() do host retorna true
            )}, {
            'Check database': (
                'workflow.steps.util.plan.StartReplicationNewInfra',  # run mysql_foxha_57_start_replication.sh
                'workflow.steps.util.database.CheckIsUp', #
                'workflow.steps.util.database.StartMonit', # sudo systemctl start monit.service
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
                ('workflow.steps.util.ssl'
                 '.SetReplicationUserRequireSSLRollbackIfRunning'),
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
                'workflow.steps.util.database.ConfigurePrometheusMonitoring'
            )}, {
            'Create Extra DNS': (
                'workflow.steps.util.database.CreateExtraDNS',
            )}, {
            'Update Host Disk Size': (
                'workflow.steps.util.host_provider.UpdateHostRootVolumeSize',
            ),
            'Save Snapshot': (
                'workflow.steps.util.database.MakeSnapshot',
            )
        }] + self.get_configure_db_params_steps()

    def get_clone_steps(self):
        return [{
            'Creating Service Account': (
                'workflow.steps.util.host_provider.CreateServiceAccount',
                'workflow.steps.util.host_provider.SetServiceAccountRoles'
            )}, {
            'Creating virtual machine': (
                'workflow.steps.util.host_provider.AllocateIP',
                'workflow.steps.util.host_provider.CreateVirtualMachine',
            )}, {
            'Creating VIP': (
                'workflow.steps.util.vip_provider.CreateVip',
                'workflow.steps.util.vip_provider.CreateInstanceGroup',
                'workflow.steps.util.vip_provider.AddInstancesInGroup',
                'workflow.steps.util.vip_provider.CreateHeathcheck',
                'workflow.steps.util.vip_provider.CreateBackendService',
                'workflow.steps.util.vip_provider.AllocateIP',
                'workflow.steps.util.vip_provider.AllocateDNS',
                'workflow.steps.util.vip_provider.CreateForwardingRule',
                'workflow.steps.util.vip_provider.AddLoadBalanceLabels',
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
                'workflow.steps.util.volume_provider.AttachDataVolumeWithUndo',
                'workflow.steps.util.volume_provider.MountDataVolume',
                'workflow.steps.util.plan.InitializationForNewInfra',
            )}, {
            'Configure SSL': (
                'workflow.steps.util.ssl.UpdateOpenSSlLib',
                'workflow.steps.util.ssl.CreateSSLFolderRollbackIfRunning',
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
                'workflow.steps.util.ssl.UpdateExpireAtDate',
            )}, {
            'Starting database': (
                'workflow.steps.util.plan.ConfigureForNewInfra',
                'workflow.steps.util.plan.ConfigureLogForNewInfra',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.metric_collector.RestartTelegraf',
                'workflow.steps.util.database.StartRsyslog',
                'workflow.steps.util.database.CheckIsUp',
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
                ('workflow.steps.util.ssl'
                 '.SetReplicationUserRequireSSLRollbackIfRunning'),
            )}, {
            'Creating Database': (
                'workflow.steps.util.database.Clone',
                'workflow.steps.util.clone.clone_database.CloneDatabaseData'
            )}, {
            'Check ACL': (
                'workflow.steps.util.acl.BindNewInstance',
            )}, {
            'Creating monitoring and alarms': (
                'workflow.steps.util.mysql.CreateAlarmsVip',
                'workflow.steps.util.zabbix.CreateAlarms',
                'workflow.steps.util.db_monitor.CreateInfraMonitoring',
            )}, {
            'Create Extra DNS': (
                'workflow.steps.util.database.CreateExtraDNS',
            )}, {
            'Update Host Disk Size': (
                'workflow.steps.util.host_provider.UpdateHostRootVolumeSize',
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
                'workflow.steps.util.database.StopSlave',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.agents.Stop',
                'workflow.steps.util.database.StopRsyslog',
                'workflow.steps.util.metric_collector.StopTelegraf',
                'workflow.steps.util.database.CheckIsDown',
            )}, {
            'Configuring': (
                ('workflow.steps.util.mysql'
                 '.AddDiskPermissionsRestoredDiskMySQL'),
                'workflow.steps.util.mysql.UnmountOldestExportRestoreMySQL',
                'workflow.steps.util.mysql.AttachNewerExportRestoreMySQL',
                'workflow.steps.util.mysql.DetachOldestExportRestoreMySQL',
                'workflow.steps.util.mysql.MountNewerExportRestoreMySQL',
                'workflow.steps.util.disk.RemoveDeprecatedFiles',
                'workflow.steps.util.plan.ConfigureRestore',
                'workflow.steps.util.plan.ConfigureLog',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
            )}, {
            'Configure SSL': (
                'workflow.steps.util.disk.CleanSSLDir',
                ('workflow.steps.util.ssl'
                 '.CreateSSLConfForInfraEndPointIfConfigured'),
                ('workflow.steps.util.ssl'
                 '.CreateSSLConfForInstanceIPIfConfigured'),
                'workflow.steps.util.ssl.RequestSSLForInfraIfConfigured',
                'workflow.steps.util.ssl.RequestSSLForInstanceIfConfigured',
                ('workflow.steps.util.ssl'
                 '.CreateJsonRequestFileInfraIfConfigured'),
                ('workflow.steps.util.ssl'
                 '.CreateJsonRequestFileInstanceIfConfigured'),
                'workflow.steps.util.ssl.CreateCertificateInfraIfConfigured',
                ('workflow.steps.util.ssl'
                 '.CreateCertificateInstanceIfConfigured'),
                'workflow.steps.util.ssl.SetSSLFilesAccessMySQLIfConfigured',
                'workflow.steps.util.ssl.UpdateExpireAtDate',
            )}, {
            'Starting database': (
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.StopRsyslog',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.StartSlave',
                'workflow.steps.util.agents.Start',
                'workflow.steps.util.database.StartRsyslog',
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

    def get_filer_migrate_steps(self):
        return [{
            'Migrating': (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
                'workflow.steps.util.database.checkAndFixMySQLReplication',
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.CheckIfSwitchMaster',
                'workflow.steps.util.volume_provider.NewInactiveVolume',
                'workflow.steps.util.metric_collector.StopTelegraf',
                'workflow.steps.util.agents.Stop',
                'workflow.steps.util.database.StopSlave',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.StopRsyslog',
                'workflow.steps.util.database.CheckIsDown',
                'workflow.steps.util.volume_provider.AddAccessNewVolume',
                'workflow.steps.util.volume_provider.MountDataLatestVolume',
                'workflow.steps.util.volume_provider.CopyFiles',
                'workflow.steps.util.volume_provider.UnmountDataLatestVolume',
                'workflow.steps.util.volume_provider.DetachDataVolume',
                'workflow.steps.util.volume_provider.UnmountDataVolume',
                'workflow.steps.util.volume_provider.MountDataNewVolume',
                'workflow.steps.util.mysql.SetFilePermission',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.StartRsyslog',
                'workflow.steps.util.database.StartSlave',
                'workflow.steps.util.agents.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.database.WaitForReplication',
                'workflow.steps.util.metric_collector.RestartTelegraf',
                'workflow.steps.util.volume_provider.TakeSnapshotOldDisk',
                'workflow.steps.util.volume_provider.UpdateActiveDisk',
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
            )}
        ]

    def get_reinstallvm_steps(self):
        return [{
            'Disable monitoring and alarms': (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
            ),
        }] + [{
            'Reinstall VM': (
                ('workflow.steps.util.database.'
                 'checkAndFixMySQLReplicationIfRunning'),
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.StopIfRunning',
                'workflow.steps.util.database.StopRsyslogIfRunning',
                'workflow.steps.util.foreman.DeleteHost',
                'workflow.steps.util.host_provider.StopIfRunning',
                'workflow.steps.util.volume_provider.DetachDataVolume',
                'workflow.steps.util.host_provider.ReinstallTemplate',
                'workflow.steps.util.host_provider.Start',
                'workflow.steps.util.vm.WaitingBeReady',
                'workflow.steps.util.vm.UpdateOSDescription',
                'workflow.steps.util.host_provider.UpdateHostRootVolumeSize',
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
                'workflow.steps.util.volume_provider.AttachDataVolume',
                'workflow.steps.util.volume_provider.MountDataVolume',
                'workflow.steps.util.plan.Initialization',
                'workflow.steps.util.plan.Configure',
                'workflow.steps.util.plan.ConfigureLog',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
                'workflow.steps.util.database.Stop',
                ) + self.get_change_binaries_upgrade_patch_steps() + (
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.metric_collector.RestartTelegraf',
            ),
        }] + self.get_reinstallvm_steps_final() + self.get_configure_db_params_steps()

    def get_upgrade_steps(self):
        return [{
            self.get_upgrade_steps_initial_description(): (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
            ),
        }] + [{
            self.get_upgrade_steps_description(): (
                'workflow.steps.util.database.checkAndFixMySQLReplication',
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.CheckIfSwitchMaster',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.StopRsyslogIfRunning',
                'workflow.steps.util.database.CheckIsDown',
                'workflow.steps.util.foreman.DeleteHost',
                'workflow.steps.util.host_provider.Stop',
                'workflow.steps.util.volume_provider.DetachDataVolume',
                'workflow.steps.util.host_provider.InstallNewTemplate',
                'workflow.steps.util.host_provider.Start',
                'workflow.steps.util.vm.WaitingBeReady',
                'workflow.steps.util.vm.UpdateOSDescription',
                'workflow.steps.util.host_provider.UpdateHostRootVolumeSize',
            ) + self.get_upgrade_steps_extra() + (
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.metric_collector.RestartTelegraf',
            ),
        }] + self.get_upgrade_steps_final()

    def get_upgrade_steps_final(self):
        return [{
            self.get_upgrade_steps_final_description(): (
                'workflow.steps.util.db_monitor.UpdateInfraVersion',
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.DestroyAlarms',
                'workflow.steps.util.zabbix.CreateAlarmsForUpgrade',
                'workflow.steps.util.mysql.DestroyAlarmsVip',
                'workflow.steps.util.mysql.CreateAlarmsVipForUpgrade',
            ),
        }]

    def get_migrate_engines_steps(self):
        return [{
            self.get_upgrade_steps_initial_description(): (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
            ),
        }] + [{
            self.get_upgrade_steps_description(): (
                'workflow.steps.util.database.checkAndFixMySQLReplication',
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.CheckIfSwitchMaster',
                'workflow.steps.util.database.StopIfRunning',
                'workflow.steps.util.database.StopRsyslogIfRunning',
                'workflow.steps.util.database.CheckIsDown',
                'workflow.steps.util.host_provider.StopIfRunning',
                'workflow.steps.util.volume_provider.DetachDataVolume',
                ('workflow.steps.util.host_provider.'
                 'InstallMigrateEngineTemplate'),
                'workflow.steps.util.host_provider.Start',
                'workflow.steps.util.vm.WaitingBeReady',
                'workflow.steps.util.vm.UpdateOSDescription',
                'workflow.steps.util.vm.CheckHostName',
                'workflow.steps.util.puppet.WaitingBeStarted',
                'workflow.steps.util.puppet.WaitingBeDone',
                'workflow.steps.util.puppet.ExecuteIfProblem',
                'workflow.steps.util.puppet.WaitingBeDone',
                'workflow.steps.util.puppet.CheckStatus',
                'workflow.steps.util.foreman.SetupDSRC',
                'workflow.steps.util.puppet.Execute',
                'workflow.steps.util.puppet.CheckStatus',
            ) + self.get_migrate_engine_steps_extra() + (
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.host_provider.UpdateHostRootVolumeSize',
                'workflow.steps.util.metric_collector.RestartTelegraf',
            ),
        }] + self.get_migrate_engine_steps_final()

    def get_migrate_engine_steps_final(self):
        return [{
            self.get_upgrade_steps_final_description(): (
                'workflow.steps.util.db_monitor.UpdateInfraVersion',
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.DestroyAlarms',
                'workflow.steps.util.zabbix.CreateAlarmsForMigrateEngine',
                'workflow.steps.util.mysql.DestroyAlarmsVip',
                'workflow.steps.util.mysql.CreateAlarmsVipForMigradeEngine',
            ),
        }]

    def get_upgrade_steps_extra(self):
        return (
            'workflow.steps.util.volume_provider.AttachDataVolume',
            'workflow.steps.util.volume_provider.MountDataVolume',
            'workflow.steps.util.plan.InitializationForUpgrade',
            'workflow.steps.util.plan.ConfigureForUpgrade',
            'workflow.steps.util.plan.ConfigureLog',
            'workflow.steps.util.metric_collector.ConfigureTelegraf',
            'workflow.steps.util.vm.CheckHostName',
            'workflow.steps.util.puppet.WaitingBeStarted',
            'workflow.steps.util.puppet.WaitingBeDone',
            'workflow.steps.util.puppet.ExecuteIfProblem',
            'workflow.steps.util.puppet.WaitingBeDone',
            'workflow.steps.util.puppet.CheckStatus',
            'workflow.steps.util.foreman.SetupDSRC',
            'workflow.steps.util.puppet.Execute',
            'workflow.steps.util.puppet.CheckStatus',
            'workflow.steps.util.mysql.SetFilePermission',
            'workflow.steps.util.plan.Configure',
            'workflow.steps.util.plan.ConfigureLog',
            'workflow.steps.util.mysql.SkipSlaveStart',
            'workflow.steps.util.mysql.DisableLogBin',
            'workflow.steps.util.database.Start',
            'workflow.steps.util.database.CheckIsUp',
            'workflow.steps.util.mysql.RunMySQLUpgrade',
            'workflow.steps.util.mysql.InstallAuditPlugin',
            'workflow.steps.util.mysql.CheckIfAuditPluginIsInstalled',
            'workflow.steps.util.database.Stop',
            'workflow.steps.util.plan.ConfigureForUpgrade',
            'workflow.steps.util.plan.ConfigureLog',
        )

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
                'workflow.steps.util.plan.ConfigureLog',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
                'workflow.steps.util.ssl.UpdateExpireAtDate',
            ),
        }] + [{
            'Restart Database': (
                'workflow.steps.util.database.checkAndFixMySQLReplication',
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.CheckIfSwitchMaster',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.metric_collector.RestartTelegraf',
                'workflow.steps.util.database.CheckIfSwitchMasterRollback',
                'workflow.steps.util.vm.ChangeMasterRollback',
                ('workflow.steps.util.database.'
                 'checkAndFixMySQLReplicationRollback'),
            ),
        }] + [{
            'Configure Replication User': (
                'workflow.steps.util.ssl.SetReplicationUserRequireSSL',
            ),
        }] + [{
            'Enabling monitoring and alarms': (
                'workflow.steps.util.db_monitor.UpdateInfraSSLMonitor',
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
            ),
        }]

    def get_update_ssl_steps(self):
        return [{
            'Disable monitoring and alarms': (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
            ),
        }] + [{
            'Disable SSL': (
                'workflow.steps.util.ssl.UnSetReplicationUserRequireSSL',
            ),
        }] + [{
            'Configure SSL': (
                'workflow.steps.util.ssl.UpdateExpireAtDateRollback',
                'workflow.steps.util.ssl.MoveSSLFolder',
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
                'workflow.steps.util.plan.ConfigureLog',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
                'workflow.steps.util.ssl.UpdateExpireAtDate',
            ),
        }] + [{
            'Restart Database': (
                'workflow.steps.util.database.checkAndFixMySQLReplication',
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.CheckIfSwitchMaster',
                'workflow.steps.util.database.Stop',
                # 'workflow.steps.util.ssl.RestoreSSLFolder4Rollback',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.metric_collector.RestartTelegraf',
                'workflow.steps.util.database.CheckIfSwitchMasterRollback',
                'workflow.steps.util.vm.ChangeMasterRollback',
                ('workflow.steps.util.database.'
                 'checkAndFixMySQLReplicationRollback'),
            ),
        }] + [{
            'Enable SSL': (
                'workflow.steps.util.ssl.SetReplicationUserRequireSSL',
            ),
        }] + [{
            'Enabling monitoring and alarms': (
                'workflow.steps.util.db_monitor.UpdateInfraSSLMonitor',
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
            ),
        }]

    def get_host_migrate_steps_cleaning_up(self):
        return (
            'workflow.steps.util.database.StopSourceDatabaseMigrate',
            'workflow.steps.util.database.StopRsyslogMigrate',
            'workflow.steps.util.volume_provider.DestroyOldEnvironment',
            'workflow.steps.util.host_provider.DestroyVirtualMachineMigrate',
        )

    def get_recreate_slave_steps(self):
        return [{
            'Recreate Slave': (
                'workflow.steps.util.database.CheckIfSwitchMaster',
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
                'workflow.steps.util.volume_provider.TakeSnapshotFromMaster',
                ('workflow.steps.util.volume_provider'
                 '.WaitSnapshotAvailableMigrate'),
                'workflow.steps.util.agents.Stop',
                'workflow.steps.util.database.StopSlaveIfRunning',
                'workflow.steps.util.database.StopIfRunning',
                'workflow.steps.util.disk.CleanDataRecreateSlave',
                'workflow.steps.util.disk.CleanReplRecreateSlave',
                'workflow.steps.util.volume_provider.AddAccessRecreateSlave',
                ('workflow.steps.util.volume_provider'
                 '.MountDataVolumeRecreateSlave'),
                'workflow.steps.util.volume_provider.CopyDataFromSnapShot',
                'workflow.steps.util.volume_provider.CopyReplFromSnapShot',
                'workflow.steps.util.volume_provider.DetachDataVolumeRecreateSlave',
                ('workflow.steps.util.volume_provider'
                 '.UmountDataVolumeRecreateSlave'),
                ('workflow.steps.util.volume_provider'
                 '.RemoveAccessRecreateSlave'),
                'workflow.steps.util.volume_provider.RemoveSnapshotMigrate',
                'workflow.steps.util.disk.RemoveDeprecatedFiles',
                'workflow.steps.util.mysql.SetFilePermission',
                'workflow.steps.util.mysql.DisableReplicationRecreateSlave',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.mysql.SetMasterRecreateSlave',
                'workflow.steps.util.mysql.EnableReplicationRecreateSlave',
                'workflow.steps.util.database.StartSlave',
                'workflow.steps.util.agents.Stop',
                'workflow.steps.util.agents.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.fox.IsReplicationOk',
                'workflow.steps.util.metric_collector.RestartTelegraf',
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
                'workflow.steps.util.database.ConfigurePrometheusMonitoring'
            )
        }] + self.get_configure_db_params_steps()

    def get_base_host_migrate_steps(self):
        return (
            'workflow.steps.util.database.checkAndFixMySQLReplication',
            'workflow.steps.util.vm.ChangeMaster',
            'workflow.steps.util.database.CheckIfSwitchMaster',
            'workflow.steps.util.host_provider.CreateVirtualMachineMigrate',
            'workflow.steps.util.vm.WaitingBeReady',
            'workflow.steps.util.vm.UpdateOSDescription',
            'workflow.steps.util.host_provider.UpdateHostRootVolumeSize',
            'workflow.steps.util.puppet.WaitingBeStarted',
            'workflow.steps.util.puppet.WaitingBeDone',
            'workflow.steps.util.puppet.ExecuteIfProblem',
            'workflow.steps.util.puppet.WaitingBeDone',
            'workflow.steps.util.puppet.CheckStatus',
            'workflow.steps.util.foreman.SetupDSRC',
            'workflow.steps.util.puppet.Execute',
            'workflow.steps.util.puppet.CheckStatus',
            'workflow.steps.util.volume_provider.NewVolume',
            'workflow.steps.util.volume_provider.AttachDataVolume',
            'workflow.steps.util.volume_provider.MountDataVolume',
            'workflow.steps.util.volume_provider.TakeSnapshotMigrate',
            'workflow.steps.util.volume_provider.WaitSnapshotAvailableMigrate',
            'workflow.steps.util.volume_provider.AddAccessMigrate',
            'workflow.steps.util.volume_provider.MountDataVolumeMigrate',
            'workflow.steps.util.volume_provider.CopyFilesMigrate',
            'workflow.steps.util.volume_provider.DetachDataVolumeMigrate',
            'workflow.steps.util.volume_provider.UmountDataVolumeMigrate',
            'workflow.steps.util.volume_provider.RemoveAccessMigrate',
            'workflow.steps.util.volume_provider.RemoveSnapshotMigrate',
            'workflow.steps.util.disk.RemoveDeprecatedFiles',
            'workflow.steps.util.plan.ConfigureForNewInfra',
            'workflow.steps.util.plan.ConfigureLogForNewInfra',
            'workflow.steps.util.mysql.SetFilePermission',
            ) + self.get_change_binaries_upgrade_patch_steps() + (
            'workflow.steps.util.database.Start',
            'workflow.steps.util.database.CheckIsUp',
            'workflow.steps.util.database.StartMonit',
            'workflow.steps.util.vm.CheckAccessToMaster',
            'workflow.steps.util.vm.CheckAccessFromMaster',
            'workflow.steps.util.acl.ReplicateAclsMigrate',
            'workflow.steps.util.mysql.SetReplicationHostMigrate',
            'workflow.steps.util.fox.RemoveNodeMigrate',
            'workflow.steps.util.fox.ConfigureNodeMigrate',
            'workflow.steps.util.vip_provider.UpdateVipReals',
            'workflow.steps.util.fox.IsReplicationOk',
            'workflow.steps.util.zabbix.DestroyAlarms',
            'workflow.steps.util.dns.ChangeEndpoint',
            'workflow.steps.util.dns.CheckIsReady',
            'workflow.steps.util.ssl.UpdateOpenSSlLibIfConfigured',
            'workflow.steps.util.ssl.CreateSSLFolderIfConfigured',
            ('workflow.steps.util.ssl'
             '.CreateSSLConfForInfraEndPointIfConfigured'),
            'workflow.steps.util.ssl.CreateSSLConfForInstanceIPIfConfigured',
            'workflow.steps.util.ssl.RequestSSLForInfraIfConfigured',
            'workflow.steps.util.ssl.RequestSSLForInstanceIfConfigured',
            'workflow.steps.util.ssl.CreateJsonRequestFileInfraIfConfigured',
            ('workflow.steps.util.ssl'
             '.CreateJsonRequestFileInstanceIfConfigured'),
            'workflow.steps.util.ssl.CreateCertificateInfraIfConfigured',
            'workflow.steps.util.ssl.CreateCertificateInstanceIfConfigured',
            'workflow.steps.util.ssl.SetSSLFilesAccessMySQLIfConfigured',
            'workflow.steps.util.ssl.UpdateExpireAtDate',
            'workflow.steps.util.metric_collector.ConfigureTelegraf',
            'workflow.steps.util.metric_collector.RestartTelegraf',
            'workflow.steps.util.zabbix.CreateAlarms',
            'workflow.steps.util.disk.ChangeSnapshotOwner',
        )

    def get_base_database_migrate_steps(self):
        return (
            'workflow.steps.util.database.checkAndFixMySQLReplication',
            'workflow.steps.util.vm.ChangeMasterMigrate',
            'workflow.steps.util.database.CheckIfSwitchMasterMigrate',
            'workflow.steps.util.host_provider.CreateVirtualMachineMigrate',
            'workflow.steps.util.volume_provider.NewVolume',
            'workflow.steps.util.vm.WaitingBeReady',
            'workflow.steps.util.vm.UpdateOSDescription',
            'workflow.steps.util.host_provider.UpdateHostRootVolumeSize',
            'workflow.steps.util.volume_provider.AttachDataVolume',
            'workflow.steps.util.volume_provider.MountDataVolume',
            'workflow.steps.util.volume_provider.TakeSnapshotMigrate',
            'workflow.steps.util.volume_provider.WaitSnapshotAvailableMigrate',
            'workflow.steps.util.volume_provider.AddHostsAllowDatabaseMigrate',
            'workflow.steps.util.volume_provider.CreatePubKeyMigrate',
            'workflow.steps.util.volume_provider.NewVolumeMigrate',
            'workflow.steps.util.volume_provider.ScpFromSnapshotMigrate',
            ('workflow.steps.util.volume_provider'
             '.RemoveHostsAllowDatabaseMigrate'),
            'workflow.steps.util.volume_provider.RemovePubKeyMigrate',
            'workflow.steps.util.disk.RemoveDeprecatedFiles',
            'workflow.steps.util.plan.ConfigureForNewInfra',
            'workflow.steps.util.plan.ConfigureLogForNewInfra',
            'workflow.steps.util.mysql.SetServeridMigrate',
            'workflow.steps.util.mysql.SetFilePermission',
            'workflow.steps.util.mysql.DisableReplication',
            'workflow.steps.util.database.Start',
            'workflow.steps.util.database.CheckIsUp',
            'workflow.steps.util.mysql.SetReplicationLastInstanceMigrate',
            'workflow.steps.util.mysql.EnableReplication',
            'workflow.steps.util.database.StartMonit',
            'workflow.steps.util.vm.CheckAccessToMaster',
            'workflow.steps.util.vm.CheckAccessFromMaster',
            'workflow.steps.util.acl.ReplicateAclsMigrate',
            'workflow.steps.util.zabbix.DisableAlarms',
            'workflow.steps.util.db_monitor.DisableMonitoring',
            'workflow.steps.util.mysql.SetReadOnlyMigrate',

        )

    def get_host_migrate_steps(self):
        return [{
            'Migrating':
                self.get_base_host_migrate_steps() +
                self.get_host_migrate_steps_cleaning_up()
        }]

    def get_database_migrate_steps(self):
        return [{
            'Creating new hosts': self.get_base_database_migrate_steps()
        }, {
            'Check Replication': (
                'workflow.steps.util.fox.IsReplicationOkMigrate',
            )
        }, {
            'Configure Replication': (
                'workflow.steps.util.mysql.SetReplicationFirstInstanceMigrate',
            )
        }, {
            'VIP': (
                'workflow.steps.util.vip_provider.CreateVipMigrate',
                'workflow.steps.util.vip_provider.UpdateVipRealsMigrate',
            )
        }, {
            'Change Endpoint': (
                'workflow.steps.util.dns.ChangeEndpoint',
                'workflow.steps.util.dns.UnregisterDNSVipMigrate',
                'workflow.steps.util.dns.RegisterDNSVipMigrate',
                'workflow.steps.util.dns.ChangeVipEndpoint',
                'workflow.steps.util.dns.CheckIsReady',
            )
        }, {
            'Set serverid': (
                'workflow.steps.util.mysql.SetServerid',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.CheckIsDown',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
            )
        }, {
            'Set Instance Read Write': (
                'workflow.steps.util.mysql.SetReadWriteMigrate',
            )
        }, {
            'Remove Old FOX': (
                'workflow.steps.util.fox.RemoveNodeMigrate',
                'workflow.steps.util.fox.RemoveGroupMigrate',
            )
        }, {
            'Create new FOX': (
                'workflow.steps.util.fox.ConfigureGroupMigrate',
                'workflow.steps.util.fox.ConfigureNodeDatabaseMigrate',
            )
        }, {
            'SSL': (
                'workflow.steps.util.ssl.UpdateOpenSSlLibIfConfigured',
                'workflow.steps.util.ssl.CreateSSLFolderIfConfigured',
                ('workflow.steps.util.ssl'
                 '.CreateSSLConfForInfraEndPointIfConfigured'),
                ('workflow.steps.util.ssl'
                 '.CreateSSLConfForInstanceIPIfConfigured'),
                'workflow.steps.util.ssl.RequestSSLForInfraIfConfigured',
                'workflow.steps.util.ssl.RequestSSLForInstanceIfConfigured',
                ('workflow.steps.util.ssl'
                 '.CreateJsonRequestFileInfraIfConfigured'),
                ('workflow.steps.util.ssl'
                 '.CreateJsonRequestFileInstanceIfConfigured'),
                'workflow.steps.util.ssl.CreateCertificateInfraIfConfigured',
                ('workflow.steps.util.ssl'
                 '.CreateCertificateInstanceIfConfigured'),
                'workflow.steps.util.ssl.SetSSLFilesAccessMySQLIfConfigured',
                'workflow.steps.util.ssl.UpdateExpireAtDate',
            )
        }, {
            'Telegraf': (
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
                'workflow.steps.util.metric_collector.RestartTelegraf',)
        }, {
            'Zabbix': (
                'workflow.steps.util.zabbix.DestroyAlarms',
                'workflow.steps.util.zabbix.CreateAlarms',
                ('workflow.steps.util.db_monitor'
                 '.UpdateInfraCloudDatabaseMigrate'),
                'workflow.steps.util.disk.ChangeSnapshotOwner',
            )
        }, {
            'Cleaning up': (
                'workflow.steps.util.volume_provider.RemoveSnapshotMigrate',
                'workflow.steps.util.vip_provider.DestroyVipMigrate',
                ) + self.get_host_migrate_steps_cleaning_up()
        }]

    def get_database_migrate_steps_stage_1(self):
        return [{
            'Creating Service Account': (
                'workflow.steps.util.host_provider.CreateServiceAccount',
                'workflow.steps.util.host_provider.SetServiceAccountRoles'
            )}, {
            'Creating virtual machine': (
                'workflow.steps.util.host_provider.AllocateIP',
                'workflow.steps.util.host_provider.CreateVirtualMachineMigrate',
                'workflow.steps.util.infra.MigrationCreateInstance',
            )}, {
            'Creating disk': (
                'workflow.steps.util.volume_provider.NewVolume',
            )}, {
            'Waiting VMs': (
                'workflow.steps.util.vm.WaitingBeReady',
                'workflow.steps.util.vm.UpdateOSDescription',
                'workflow.steps.util.host_provider.UpdateHostRootVolumeSize',
            )}, {
            'Check patch': (
                ) + self.get_change_binaries_upgrade_patch_steps() + (
            )}, {
            'Configuring database': (
                'workflow.steps.util.volume_provider.AttachDataVolume',
                'workflow.steps.util.volume_provider.MountDataVolume',
                'workflow.steps.util.plan.Initialization',
                'workflow.steps.util.plan.ConfigureLog',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
                'workflow.steps.util.plan.Configure',
            )}, {
            'Configure SSL lib and folder': (
                ) + self.get_configure_ssl_libs_and_folder_steps() + (
            )}, {
            'Configure SSL (IP)': (
                ) + self.get_configure_ssl_ip_steps() + (
            )}, {
            'Start database and check access': (
                'workflow.steps.util.database.Start',
                'workflow.steps.util.vm.CheckAccessToMaster',
                'workflow.steps.util.vm.CheckAccessFromMaster',
            )}, {
            'Backup and restore': (
                'workflow.steps.util.volume_provider.TakeSnapshotMigrate',
                'workflow.steps.util.volume_provider.WaitSnapshotAvailableMigrate',
                'workflow.steps.util.volume_provider.AddHostsAllowMigrateBackupHost',
                'workflow.steps.util.volume_provider.CreatePubKeyMigrateBackupHost',
                'workflow.steps.util.database.StopWithoutUndo',
                'workflow.steps.util.database.CheckIsDown',
                'workflow.steps.util.disk.CleanDataMigrate',
                'workflow.steps.util.volume_provider.NewVolumeMigrateOriginalHost',
                'workflow.steps.util.volume_provider.AttachDataLatestVolumeMigrate',
                'workflow.steps.util.volume_provider.MountDataLatestVolumeMigrate',
                'workflow.steps.util.volume_provider.RsyncFromSnapshotMigrateBackupHost',
                'workflow.steps.util.volume_provider.WaitRsyncFromSnapshotDatabaseMigrate',
                'workflow.steps.util.volume_provider.RemovePubKeyMigrateHostMigrate',
                'workflow.steps.util.volume_provider.RemoveHostsAllowMigrateBackupHost',
                'workflow.steps.util.volume_provider.UmountDataLatestVolumeMigrate',
                'workflow.steps.util.volume_provider.DetachDataLatestVolumeMigrate',
                'workflow.steps.util.volume_provider.DeleteVolumeMigrateOriginalHost',
                'workflow.steps.util.disk.RemoveDeprecatedFiles',
                'workflow.steps.util.plan.ConfigureForNewInfra',
                'workflow.steps.util.plan.ConfigureLogForNewInfra',
                'workflow.steps.util.mysql.SetServeridMigrate',
                'workflow.steps.util.mysql.SetFilePermission',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.infra.EnableFutureInstances',
            )}, {
            'Creating VIP': (
                'workflow.steps.util.vip_provider.CreateVip',
                'workflow.steps.util.vip_provider.CreateInstanceGroup',
                'workflow.steps.util.vip_provider.AddInstancesInGroup',
                'workflow.steps.util.vip_provider.CreateHeathcheck',
                'workflow.steps.util.vip_provider.CreateBackendService',
                'workflow.steps.util.vip_provider.AllocateIPMigrate',
                'workflow.steps.util.vip_provider.CreateForwardingRule',
                'workflow.steps.util.vip_provider.AddLoadBalanceLabels',
                #'workflow.steps.util.dns.RegisterDNSVip',
            )}, {
            'Replicate ACL': (
                'workflow.steps.util.acl.ReplicateAclsMigrate',
                'workflow.steps.util.acl.ReplicateVipAclsMigrate',
                'workflow.steps.util.acl.BindNewInstanceDatabaseMigrate',
            )}, {
            'Start telegraf and rsyslog': (
                'workflow.steps.util.database.StartRsyslog',
                'workflow.steps.util.metric_collector.RestartTelegraf',
            )}, {
             'Check puppet': (
                 'workflow.steps.util.puppet.WaitingBeStarted',
                 'workflow.steps.util.puppet.WaitingBeDone',
                 'workflow.steps.util.puppet.ExecuteIfProblem',
                 'workflow.steps.util.puppet.WaitingBeDone',
                 'workflow.steps.util.puppet.CheckStatus',
             )}, {
             'Configure foreman': (
                 'workflow.steps.util.foreman.SetupDSRCMigrate',
             )}, {
             'Running puppet': (
                 'workflow.steps.util.puppet.Execute',
                 'workflow.steps.util.puppet.CheckStatus',
             )}, {
            'Reconfigure FOX nodes': (
                'workflow.steps.util.fox.MigrationAddNodeDestinyInstanceDisabled',
            )}, {
            #'Wait replication': (
            # TODO CHECK IF should use WaitForReplication or CheckReplicationDBMigrate
            #    'workflow.steps.util.database.WaitForReplication',
            #)}, {
            'Check Replication': (
                'workflow.steps.util.mysql.CheckReplicationDBMigrate',
            )}
        ]

    def get_database_migrate_steps_stage_2(self):
        return [{
            'Destroy Alarms': (
                'workflow.steps.util.zabbix.DestroyAlarmsDatabaseMigrate',
                'workflow.steps.util.mysql.DestroyAlarmsVipDatabaseMigrate',
            )}, {
            'Check Replication': (
                'workflow.steps.util.mysql.CheckReplicationDBMigrate',
            )}, {
            'Set Instances Read Only': (
                'workflow.steps.util.mysql.SetSourceInstancesReadOnlyMigrate',
            )}, {
            'Check Replication': (
                'workflow.steps.util.mysql.CheckReplicationDBMigrate',
            )}, {
            'Reconfigure Replication': (
                'workflow.steps.util.mysql.ReconfigureReplicationDBMigrate',
            )}, {
            'Check Replication': (
                'workflow.steps.util.mysql.CheckReplicationDBMigrate',
            )}, {
            'Set Instance Read Write': (
                'workflow.steps.util.mysql.SetFirstTargetInstanceReadWriteMigrate',
            )}, {
            'Reconfigure FOX nodes': (
                'workflow.steps.util.fox.MigrationAddNodeSourceInstanceEnabledRollback',
            )}, {
            'Configure Telegraf': (
                'workflow.steps.util.metric_collector.RestartTelegrafRollback',
                'workflow.steps.util.metric_collector.ConfigureTelegrafRollback',
                'workflow.steps.util.metric_collector.RestartTelegrafSourceDBMigrateRollback',
                'workflow.steps.util.metric_collector.ConfigureTelegrafSourceDBMigrateRollback',
            )}, {
            'Check DNS when Rollback': (
                'workflow.steps.util.dns.CheckIsReadyDBMigrateRollback',
                'workflow.steps.util.dns.CheckVipDMSIsReadyDBMigrateRollback',
            )}, {
            'Update DNS': (
                'workflow.steps.util.dns.ChangeEndpointDBMigrate',
                'workflow.steps.util.dns.ChangeVipEndpointDBMigrate',
                'workflow.steps.util.dns.ChangeInfraVipEndpointDBMigrate',
            )}, {
            'Check DNS': (
                'workflow.steps.util.dns.CheckIsReadyDBMigrate',
                'workflow.steps.util.dns.CheckVipDNSIsReadyDBMigrate',
            )}, {
            'Reconfigure FOX group': (
                'workflow.steps.util.fox.RecreateGroupDatabaseMigrate',
            )}, {
            'Reconfigure FOX nodes': (
                'workflow.steps.util.fox.MigrationAddNodeDestinyInstanceEnabled',
            )}, {
            'Configure SSL (DNS)': (
                ) + self.get_configure_ssl_dns_steps() + (
            )}, {
            'Restart Database': (
                'workflow.steps.util.vm.ChangeMasterDatabaseMigrate',
                'workflow.steps.util.database.CheckIfSwitchMasterDatabaseMigrate',
                'workflow.steps.util.database.StopWithoutUndo',
                'workflow.steps.util.database.CheckIsDown',
                'workflow.steps.util.database.StartWithoutUndo',
                'workflow.steps.util.database.CheckIsUp',
            )}, {
            'Configure Telegraf': (
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
                'workflow.steps.util.metric_collector.RestartTelegraf',
                'workflow.steps.util.metric_collector.ConfigureTelegrafSourceDBMigrate',
                'workflow.steps.util.metric_collector.RestartTelegrafSourceDBMigrate',
            )}, {
            'Recreate Alarms': (
                'workflow.steps.util.zabbix.CreateAlarmsDatabaseMigrate',
                'workflow.steps.util.mysql.CreateAlarmsVip',
                'workflow.steps.util.db_monitor.UpdateInfraCloudDatabaseMigrate',
            )}
        ]

    def get_database_migrate_steps_stage_3(self):
        return [{
            'Remove FOX source nodes': (
                'workflow.steps.util.fox.MigrationRemoveNodeSourceInstance',
            )}, {
            'Disable and Stop Source instance':(
                'workflow.steps.util.database.StopSourceDatabaseMigrate',
                'workflow.steps.util.infra.DisableSourceInstances',
                'workflow.steps.util.database.StopRsyslogMigrate',
            )}, {
            'Remove Source VIP': (
                'workflow.steps.util.vip_provider.DestroySourceForwardingRuleMigrate',
                'workflow.steps.util.vip_provider.DestroySourceBackendServiceMigrate',
                'workflow.steps.util.vip_provider.DestroySourceHeathcheckMigrate',
                'workflow.steps.util.vip_provider.DestroySourceInstanceGroupMigrate',
                'workflow.steps.util.vip_provider.DestroySourceIPMigrateMigrate',
                'workflow.steps.util.vip_provider.DestroySourceVipDatabaseMigrate',
            )}, {
            'Removing Disks': (
                'workflow.steps.util.volume_provider.DestroyOldEnvironment',
            )}, {
            'Cleaning up': (
                'workflow.steps.util.host_provider.DestroyVirtualMachineMigrate',
                'workflow.steps.util.host_provider.DestroyIPMigrate',
                'workflow.steps.util.host_provider.DestroyServiceAccountMigrate',
            )}
        ]

    def get_region_migrate_steps_stage_1(self):
        return [{
            'Creating Service Account': (
                'workflow.steps.util.host_provider.CreateServiceAccount',
                'workflow.steps.util.host_provider.SetServiceAccountRoles'
            )}, {
            'Creating virtual machine': (
                'workflow.steps.util.host_provider.AllocateIPRegionMigrate',
                'workflow.steps.util.host_provider.CreateVirtualMachineRegionMigrate',
                'workflow.steps.util.infra.MigrationCreateInstance',
            )}, {
            'Creating disk': (
                'workflow.steps.util.volume_provider.NewVolume',
            )}, {
            'Waiting VMs': (
                'workflow.steps.util.vm.WaitingBeReady',
                'workflow.steps.util.vm.UpdateOSDescription',
                'workflow.steps.util.host_provider.UpdateHostRootVolumeSize',
            )}, {
            'Check patch': (
                           ) + self.get_change_binaries_upgrade_patch_steps() + (
                           )}, {
            'Configuring database': (
                'workflow.steps.util.volume_provider.AttachDataVolume',
                'workflow.steps.util.volume_provider.MountDataVolume',
                'workflow.steps.util.plan.Initialization',
                'workflow.steps.util.plan.ConfigureLog',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
                'workflow.steps.util.plan.Configure',
            )}, {
            'Configure SSL lib and folder': (
                                            ) + self.get_configure_ssl_libs_and_folder_steps() + (
                                            )}, {
            'Configure SSL (IP)': (
                                  ) + self.get_configure_ssl_ip_steps() + (
                                  )}, {
            'Start database and check access': (
                'workflow.steps.util.database.Start',
                'workflow.steps.util.vm.CheckAccessToMaster',
                'workflow.steps.util.vm.CheckAccessFromMaster',
            )}, {
            'Backup and restore': (
                'workflow.steps.util.volume_provider.TakeSnapshotMigrate',
                'workflow.steps.util.volume_provider.WaitSnapshotAvailableMigrate',
                'workflow.steps.util.volume_provider.AddHostsAllowMigrateBackupHost',
                'workflow.steps.util.volume_provider.CreatePubKeyMigrateBackupHost',
                'workflow.steps.util.database.StopWithoutUndo',
                'workflow.steps.util.database.CheckIsDown',
                'workflow.steps.util.disk.CleanDataMigrate',
                'workflow.steps.util.volume_provider.NewVolumeMigrateOriginalHost',
                'workflow.steps.util.volume_provider.AttachDataLatestVolumeMigrate',
                'workflow.steps.util.volume_provider.MountDataLatestVolumeMigrate',
                'workflow.steps.util.volume_provider.RsyncFromSnapshotMigrateBackupHost',
                'workflow.steps.util.volume_provider.WaitRsyncFromSnapshotDatabaseMigrate',
                'workflow.steps.util.volume_provider.RemovePubKeyMigrateHostMigrate',
                'workflow.steps.util.volume_provider.RemoveHostsAllowMigrateBackupHost',
                'workflow.steps.util.volume_provider.UmountDataLatestVolumeMigrate',
                'workflow.steps.util.volume_provider.DetachDataLatestVolumeMigrate',
                'workflow.steps.util.volume_provider.DeleteVolumeMigrateOriginalHost',
                'workflow.steps.util.disk.RemoveDeprecatedFiles',
                'workflow.steps.util.plan.ConfigureForNewInfra',
                'workflow.steps.util.plan.ConfigureLogForNewInfra',
                'workflow.steps.util.mysql.SetServeridMigrate',
                'workflow.steps.util.mysql.SetFilePermission',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.infra.EnableFutureInstances',
            )}, {
            'Creating VIP': (
                'workflow.steps.util.vip_provider.CreateVip',
                'workflow.steps.util.vip_provider.CreateInstanceGroup',
                'workflow.steps.util.vip_provider.AddInstancesInGroup',
                'workflow.steps.util.vip_provider.CreateHeathcheck',
                'workflow.steps.util.vip_provider.CreateBackendService',
                'workflow.steps.util.vip_provider.AllocateIPMigrate',
                'workflow.steps.util.vip_provider.CreateForwardingRule',
                'workflow.steps.util.vip_provider.AddLoadBalanceLabels',
                # 'workflow.steps.util.dns.RegisterDNSVip',
            )}, {
            'Replicate ACL': (
                'workflow.steps.util.acl.ReplicateAclsMigrate',
                'workflow.steps.util.acl.ReplicateVipAclsMigrate',
                'workflow.steps.util.acl.BindNewInstanceDatabaseMigrate',
            )}, {
            'Start telegraf and rsyslog': (
                'workflow.steps.util.database.StartRsyslog',
                'workflow.steps.util.metric_collector.RestartTelegraf',
            )}, {
            'Check puppet': (
                'workflow.steps.util.puppet.WaitingBeStarted',
                'workflow.steps.util.puppet.WaitingBeDone',
                'workflow.steps.util.puppet.ExecuteIfProblem',
                'workflow.steps.util.puppet.WaitingBeDone',
                'workflow.steps.util.puppet.CheckStatus',
            )}, {
            'Configure foreman': (
                'workflow.steps.util.foreman.SetupDSRCMigrate',
            )}, {
            'Running puppet': (
                'workflow.steps.util.puppet.Execute',
                'workflow.steps.util.puppet.CheckStatus',
            )}, {
            'Reconfigure FOX nodes': (
                'workflow.steps.util.fox.MigrationAddNodeDestinyInstanceDisabled',
            )}, {
            # 'Wait replication': (
            # TODO CHECK IF should use WaitForReplication or CheckReplicationDBMigrate
            #    'workflow.steps.util.database.WaitForReplication',
            # )}, {
            'Check Replication': (
                'workflow.steps.util.mysql.CheckReplicationDBMigrate',
            )}
        ]

    def get_region_migrate_steps_stage_2(self):
        return [{
            'Destroy Alarms': (
                'workflow.steps.util.zabbix.DestroyAlarmsDatabaseMigrate',
                'workflow.steps.util.mysql.DestroyAlarmsVipDatabaseMigrate',
            )}, {
            'Check Replication': (
                'workflow.steps.util.mysql.CheckReplicationDBMigrate',
            )}, {
            'Set Instances Read Only': (
                'workflow.steps.util.mysql.SetSourceInstancesReadOnlyMigrate',
            )}, {
            'Check Replication': (
                'workflow.steps.util.mysql.CheckReplicationDBMigrate',
            )}, {
            'Reconfigure Replication': (
                'workflow.steps.util.mysql.ReconfigureReplicationDBMigrate',
            )}, {
            'Check Replication': (
                'workflow.steps.util.mysql.CheckReplicationDBMigrate',
            )}, {
            'Set Instance Read Write': (
                'workflow.steps.util.mysql.SetFirstTargetInstanceReadWriteMigrate',
            )}, {
            'Reconfigure FOX nodes': (
                'workflow.steps.util.fox.MigrationAddNodeSourceInstanceEnabledRollback',
            )}, {
            'Configure Telegraf': (
                'workflow.steps.util.metric_collector.RestartTelegrafRollback',
                'workflow.steps.util.metric_collector.ConfigureTelegrafRollback',
                'workflow.steps.util.metric_collector.RestartTelegrafSourceDBMigrateRollback',
                'workflow.steps.util.metric_collector.ConfigureTelegrafSourceDBMigrateRollback',
            )}, {
            'Check DNS when Rollback': (
                'workflow.steps.util.dns.CheckIsReadyDBMigrateRollback',
                'workflow.steps.util.dns.CheckVipDMSIsReadyDBMigrateRollback',
            )}, {
            'Update DNS': (
                'workflow.steps.util.dns.ChangeEndpointDBMigrate',
                'workflow.steps.util.dns.ChangeVipEndpointDBMigrate',
                'workflow.steps.util.dns.ChangeInfraVipEndpointDBMigrate',
            )}, {
            'Check DNS': (
                'workflow.steps.util.dns.CheckIsReadyDBMigrate',
                'workflow.steps.util.dns.CheckVipDNSIsReadyDBMigrate',
            )}, {
            'Reconfigure FOX group': (
                'workflow.steps.util.fox.RecreateGroupDatabaseMigrate',
            )}, {
            'Reconfigure FOX nodes': (
                'workflow.steps.util.fox.MigrationAddNodeDestinyInstanceEnabled',
            )}, {
            'Configure SSL (DNS)': (
                                   ) + self.get_configure_ssl_dns_steps() + (
                                   )}, {
            'Restart Database': (
                'workflow.steps.util.vm.ChangeMasterDatabaseMigrate',
                'workflow.steps.util.database.CheckIfSwitchMasterDatabaseMigrate',
                'workflow.steps.util.database.StopWithoutUndo',
                'workflow.steps.util.database.CheckIsDown',
                'workflow.steps.util.database.StartWithoutUndo',
                'workflow.steps.util.database.CheckIsUp',
            )}, {
            'Configure Telegraf': (
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
                'workflow.steps.util.metric_collector.RestartTelegraf',
                'workflow.steps.util.metric_collector.ConfigureTelegrafSourceDBMigrate',
                'workflow.steps.util.metric_collector.RestartTelegrafSourceDBMigrate',
            )}, {
            'Recreate Alarms': (
                'workflow.steps.util.zabbix.CreateAlarmsDatabaseMigrate',
                'workflow.steps.util.mysql.CreateAlarmsVip',
                'workflow.steps.util.db_monitor.UpdateInfraCloudDatabaseMigrate',
            )}
        ]

    def get_region_migrate_steps_stage_3(self):
        return [{
            'Remove FOX source nodes': (
                'workflow.steps.util.fox.MigrationRemoveNodeSourceInstance',
            )}, {
            'Disable and Stop Source instance': (
                'workflow.steps.util.database.StopSourceDatabaseMigrate',
                'workflow.steps.util.infra.DisableSourceInstances',
                'workflow.steps.util.database.StopRsyslogMigrate',
            )}, {
            'Remove Source VIP': (
                'workflow.steps.util.vip_provider.DestroySourceForwardingRuleMigrate',
                'workflow.steps.util.vip_provider.DestroySourceBackendServiceMigrate',
                'workflow.steps.util.vip_provider.DestroySourceHeathcheckMigrate',
                'workflow.steps.util.vip_provider.DestroySourceInstanceGroupMigrate',
                'workflow.steps.util.vip_provider.DestroySourceIPMigrateMigrate',
                'workflow.steps.util.vip_provider.DestroySourceVipDatabaseMigrate',
            )}, {
            'Removing Disks': (
                'workflow.steps.util.volume_provider.DestroyOldEnvironment',
            )}, {
            'Cleaning up': (
                'workflow.steps.util.host_provider.DestroyVirtualMachineMigrate',
                'workflow.steps.util.host_provider.DestroyIPMigrate',
                'workflow.steps.util.host_provider.DestroyServiceAccountMigrate',
            )}
        ]


class MySQLFoxHAAWS(MySQLFoxHA):
    def get_deploy_steps(self):
        return [{
            'Creating Service Account': (
                'workflow.steps.util.host_provider.CreateServiceAccount',
                'workflow.steps.util.host_provider.SetServiceAccountRoles'
            )}, {
            'Creating virtual machine': (
                'workflow.steps.util.host_provider.CreateVirtualMachine',
            )}, {
            'Creating VIP': (
                'workflow.steps.util.vip_provider.CreateVip',
                'workflow.steps.util.vip_provider.AddReal',
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
            'Check DNS': (
                'workflow.steps.util.dns.CheckIsReady',
            )}, {
            'Configuring database': (
                'workflow.steps.util.volume_provider.AttachDataVolumeWithUndo',
                'workflow.steps.util.volume_provider.MountDataVolume',
                'workflow.steps.util.plan.InitializationForNewInfra',
            )}, {
            'Configure SSL': (
                'workflow.steps.util.ssl.UpdateOpenSSlLib',
                'workflow.steps.util.ssl.CreateSSLFolderRollbackIfRunning',
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
                'workflow.steps.util.ssl.UpdateExpireAtDate',
            )}, {
            'Starting database': (
                'workflow.steps.util.plan.ConfigureForNewInfra',
                'workflow.steps.util.plan.ConfigureLogForNewInfra',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.metric_collector.RestartTelegraf',
                'workflow.steps.util.database.StartRsyslog',
                'workflow.steps.util.database.CheckIsUp',
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
                ('workflow.steps.util.ssl'
                 '.SetReplicationUserRequireSSLRollbackIfRunning'),
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
                'workflow.steps.util.database.ConfigurePrometheusMonitoring'
            )}, {
            'Check Vip': (
                'workflow.steps.util.vip_provider.WaitVipReady',
            )}, {
            'Create Extra DNS': (
                'workflow.steps.util.database.CreateExtraDNS',
            )}, {
            'Update Host Disk Size': (
                'workflow.steps.util.host_provider.UpdateHostRootVolumeSize',
            ),
            'Save Snapshot': (
                'workflow.steps.util.database.MakeSnapshot',
            )
        }]

    def get_clone_steps(self):
        return [{
            'Creating virtual machine': (
                'workflow.steps.util.host_provider.CreateVirtualMachine',
            )}, {
            'Creating VIP': (
                'workflow.steps.util.vip_provider.CreateVip',
                'workflow.steps.util.vip_provider.AddReal',
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
            'Check DNS': (
                'workflow.steps.util.dns.CheckIsReady',
            )}, {
            'Configuring database': (
                'workflow.steps.util.volume_provider.AttachDataVolume',
                'workflow.steps.util.volume_provider.MountDataVolume',
                'workflow.steps.util.plan.InitializationForNewInfra',
            )}, {
            'Configure SSL': (
                'workflow.steps.util.ssl.UpdateOpenSSlLib',
                'workflow.steps.util.ssl.CreateSSLFolderRollbackIfRunning',
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
                'workflow.steps.util.ssl.UpdateExpireAtDate',
            )}, {
            'Starting database': (
                'workflow.steps.util.plan.ConfigureForNewInfra',
                'workflow.steps.util.plan.ConfigureLogForNewInfra',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.metric_collector.RestartTelegraf',
                'workflow.steps.util.database.StartRsyslog',
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
                ('workflow.steps.util.ssl'
                 '.SetReplicationUserRequireSSLRollbackIfRunning'),
            )}, {
            'Creating Database': (
                'workflow.steps.util.database.Clone',
                'workflow.steps.util.clone.clone_database.CloneDatabaseData'
            )}, {
            'Check ACL': (
                'workflow.steps.util.acl.BindNewInstance',
            )}, {
            'Creating monitoring and alarms': (
                'workflow.steps.util.mysql.CreateAlarmsVip',
                'workflow.steps.util.zabbix.CreateAlarms',
                'workflow.steps.util.db_monitor.CreateInfraMonitoring',
            )}, {
            'Check Vip': (
                'workflow.steps.util.vip_provider.WaitVipReady',
            )}, {
            'Create Extra DNS': (
                'workflow.steps.util.database.CreateExtraDNS',
            )}, {
            'Update Host Disk Size': (
                'workflow.steps.util.host_provider.UpdateHostRootVolumeSize',
            )
        }]

    def get_host_migrate_steps_cleaning_up(self):
        return (
            'workflow.steps.util.database.StopSourceDatabaseMigrate',
            'workflow.steps.util.database.StopRsyslogMigrate',
            'workflow.steps.util.volume_provider.DestroyOldEnvironment',
            'workflow.steps.util.host_provider.DestroyVirtualMachineMigrate',
        )

    def get_base_host_migrate_steps(self):
        return (
            'workflow.steps.util.database.checkAndFixMySQLReplication',
            'workflow.steps.util.vm.ChangeMaster',
            'workflow.steps.util.database.CheckIfSwitchMaster',
            'workflow.steps.util.host_provider.CreateVirtualMachineMigrate',
            'workflow.steps.util.volume_provider.TakeSnapshotMigrate',
            'workflow.steps.util.volume_provider.WaitSnapshotAvailableMigrate',
            'workflow.steps.util.volume_provider.NewVolume',
            'workflow.steps.util.vm.WaitingBeReady',
            'workflow.steps.util.vm.UpdateOSDescription',
            'workflow.steps.util.host_provider.UpdateHostRootVolumeSize',
            'workflow.steps.util.volume_provider.AttachDataVolume',
            'workflow.steps.util.volume_provider.MountDataVolume',
            'workflow.steps.util.volume_provider.RemoveSnapshotMigrate',
            'workflow.steps.util.disk.RemoveDeprecatedFiles',
            'workflow.steps.util.plan.ConfigureForNewInfra',
            'workflow.steps.util.plan.ConfigureLogForNewInfra',
            'workflow.steps.util.mysql.SetFilePermission',
            ) + self.get_change_binaries_upgrade_patch_steps() + (
            'workflow.steps.util.database.Start',
            'workflow.steps.util.database.CheckIsUp',
            'workflow.steps.util.database.StartMonit',
            'workflow.steps.util.vm.CheckAccessToMaster',
            'workflow.steps.util.vm.CheckAccessFromMaster',
            'workflow.steps.util.acl.ReplicateAclsMigrate',
            'workflow.steps.util.mysql.SetReplicationHostMigrate',
            'workflow.steps.util.fox.RemoveNodeMigrate',
            'workflow.steps.util.fox.ConfigureNodeMigrate',
            'workflow.steps.util.vip_provider.RemoveRealMigrate',
            'workflow.steps.util.vip_provider.AddReal',
            'workflow.steps.util.fox.IsReplicationOk',
            'workflow.steps.util.zabbix.DestroyAlarms',
            'workflow.steps.util.dns.ChangeEndpoint',
            'workflow.steps.util.dns.CheckIsReady',
            'workflow.steps.util.ssl.UpdateOpenSSlLibIfConfigured',
            'workflow.steps.util.ssl.CreateSSLFolderIfConfigured',
            ('workflow.steps.util.ssl'
             '.CreateSSLConfForInfraEndPointIfConfigured'),
            'workflow.steps.util.ssl.CreateSSLConfForInstanceIPIfConfigured',
            'workflow.steps.util.ssl.RequestSSLForInfraIfConfigured',
            'workflow.steps.util.ssl.RequestSSLForInstanceIfConfigured',
            'workflow.steps.util.ssl.CreateJsonRequestFileInfraIfConfigured',
            ('workflow.steps.util.ssl'
             '.CreateJsonRequestFileInstanceIfConfigured'),
            'workflow.steps.util.ssl.CreateCertificateInfraIfConfigured',
            'workflow.steps.util.ssl.CreateCertificateInstanceIfConfigured',
            'workflow.steps.util.ssl.SetSSLFilesAccessMySQLIfConfigured',
            'workflow.steps.util.ssl.UpdateExpireAtDate',
            'workflow.steps.util.metric_collector.ConfigureTelegraf',
            'workflow.steps.util.metric_collector.RestartTelegraf',
            'workflow.steps.util.zabbix.CreateAlarms',
            'workflow.steps.util.db_monitor.UpdateInfraCloudDatabaseMigrate',
            'workflow.steps.util.disk.ChangeSnapshotOwner',
        )

    def get_host_migrate_steps(self):
        return [{
            'Migrating':
                self.get_base_host_migrate_steps() +
                self.get_host_migrate_steps_cleaning_up()
        }]

    def get_base_database_migrate_steps(self):
        return (
            'workflow.steps.util.database.checkAndFixMySQLReplication',
            'workflow.steps.util.vm.ChangeMasterMigrate',
            'workflow.steps.util.database.CheckIfSwitchMasterMigrate',
            'workflow.steps.util.host_provider.CreateVirtualMachineMigrate',
            'workflow.steps.util.volume_provider.NewVolume',
            'workflow.steps.util.vm.WaitingBeReady',
            'workflow.steps.util.vm.UpdateOSDescription',
            'workflow.steps.util.host_provider.UpdateHostRootVolumeSize',
            'workflow.steps.util.volume_provider.AttachDataVolume',
            'workflow.steps.util.volume_provider.MountDataVolume',
            'workflow.steps.util.volume_provider.TakeSnapshotMigrate',
            'workflow.steps.util.volume_provider.WaitSnapshotAvailableMigrate',
            'workflow.steps.util.volume_provider.AddHostsAllowDatabaseMigrate',
            'workflow.steps.util.volume_provider.CreatePubKeyMigrate',
            ('workflow.steps.util.volume_provider'
             '.NewVolumeOnSlaveMigrateFirstNode'),
            ('workflow.steps.util.volume_provider'
             '.MountDataVolumeOnSlaveFirstNode'),
            ('workflow.steps.util.volume_provider'
             '.ScpFromSnapshotDatabaseMigrate'),
             'workflow.steps.util.volume_provider.DetachDataVolumeRecreateSlaveLastNode',
            ('workflow.steps.util.volume_provider'
             '.UmountDataVolumeOnSlaveLastNode'),
            'workflow.steps.util.volume_provider.RemoveVolumeMigrateLastNode',
            ('workflow.steps.util.volume_provider'
             '.RemoveHostsAllowDatabaseMigrate'),
            'workflow.steps.util.volume_provider.RemovePubKeyMigrate',
            'workflow.steps.util.disk.RemoveDeprecatedFiles',
            'workflow.steps.util.plan.ConfigureForNewInfra',
            'workflow.steps.util.plan.ConfigureLogForNewInfra',
            'workflow.steps.util.mysql.SetServeridMigrate',
            'workflow.steps.util.mysql.SetFilePermission',
            'workflow.steps.util.mysql.DisableReplication',
            'workflow.steps.util.database.Start',
            'workflow.steps.util.database.CheckIsUp',
            'workflow.steps.util.mysql.SetReplicationLastInstanceMigrate',
            'workflow.steps.util.mysql.EnableReplication',
            'workflow.steps.util.database.StartMonit',
            'workflow.steps.util.vm.CheckAccessToMaster',
            'workflow.steps.util.vm.CheckAccessFromMaster',
            'workflow.steps.util.acl.ReplicateAclsMigrate',
            'workflow.steps.util.mysql.SetReadOnlyMigrate',

        )

    def get_database_migrate_steps(self):
        return [{
            'Creating new hosts': self.get_base_database_migrate_steps()
        }, {
            'Wait Replication': (
                'workflow.steps.util.fox.IsReplicationOkMigrate',
            )
        }, {
            'Configure Replication': (
                'workflow.steps.util.mysql.SetReplicationFirstInstanceMigrate',
            )
        }, {
            'VIP': (
                'workflow.steps.util.vip_provider.CreateVipMigrate',
                'workflow.steps.util.vip_provider.UpdateVipRealsMigrate',
            )
        }, {
            'Configure VIP': (
                'workflow.steps.util.puppet.WaitingBeStarted',
                'workflow.steps.util.puppet.WaitingBeDone',
                'workflow.steps.util.puppet.ExecuteIfProblem',
                'workflow.steps.util.puppet.WaitingBeDone',
                'workflow.steps.util.puppet.CheckStatus',
                'workflow.steps.util.foreman.SetupDSRCMigrate',
                'workflow.steps.util.puppet.Execute',
                'workflow.steps.util.puppet.CheckStatus'
            )
        }, {
            'Change Endpoint': (
                'workflow.steps.util.dns.ChangeEndpoint',
                'workflow.steps.util.dns.UnregisterDNSVipMigrate',
                'workflow.steps.util.dns.RegisterDNSVipMigrate',
                'workflow.steps.util.dns.ChangeVipEndpoint',
                'workflow.steps.util.dns.CheckIsReady',
            )
        }, {
            'Set serverid': (
                'workflow.steps.util.mysql.SetServerid',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.CheckIsDown',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
            )
        }, {
            'Set Instance Read Write': (
                'workflow.steps.util.mysql.SetReadWriteMigrate',
            )
        }, {
            'Remove Old FOX': (
                'workflow.steps.util.fox.RemoveNodeMigrate',
                'workflow.steps.util.fox.RemoveGroupMigrate',
            )
        }, {
            'Create new FOX': (
                'workflow.steps.util.fox.ConfigureGroupMigrate',
                'workflow.steps.util.fox.ConfigureNodeDatabaseMigrate',
            )
        }, {
            'SSL': (
                'workflow.steps.util.ssl.UpdateOpenSSlLibIfConfigured',
                'workflow.steps.util.ssl.CreateSSLFolderIfConfigured',
                ('workflow.steps.util.ssl'
                 '.CreateSSLConfForInfraEndPointIfConfigured'),
                ('workflow.steps.util.ssl'
                 '.CreateSSLConfForInstanceIPIfConfigured'),
                'workflow.steps.util.ssl.RequestSSLForInfraIfConfigured',
                'workflow.steps.util.ssl.RequestSSLForInstanceIfConfigured',
                ('workflow.steps.util.ssl'
                 '.CreateJsonRequestFileInfraIfConfigured'),
                ('workflow.steps.util.ssl'
                 '.CreateJsonRequestFileInstanceIfConfigured'),
                'workflow.steps.util.ssl.CreateCertificateInfraIfConfigured',
                ('workflow.steps.util.ssl'
                 '.CreateCertificateInstanceIfConfigured'),
                'workflow.steps.util.ssl.SetSSLFilesAccessMySQLIfConfigured',
                'workflow.steps.util.ssl.UpdateExpireAtDate',
            )
        }, {
            'Telegraf': (
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
                'workflow.steps.util.metric_collector.RestartTelegraf',)
        }, {
            'Zabbix': (
                'workflow.steps.util.zabbix.DestroyAlarms',
                'workflow.steps.util.zabbix.CreateAlarms',
                'workflow.steps.util.disk.ChangeSnapshotOwner',
            )
        }, {
            'Cleaning up': (
                'workflow.steps.util.volume_provider.RemoveSnapshotMigrate',
                'workflow.steps.util.vip_provider.DestroyVipMigrate',
                ) + self.get_host_migrate_steps_cleaning_up()
        }]


class MySQLSingleGCP(MySQLSingle):

    def get_host_migrate_steps(self):
        return [{
            'Disable monitoring and alarms': (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
            )}, {
            'Stop previous database': (
                'workflow.steps.util.metric_collector.RestartTelegrafRollback',
                ('workflow.steps.util.metric_collector.'
                 'ConfigureTelegrafRollback'),
                'workflow.steps.util.database.CheckIsUpRollback',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.StopRsyslog',
                'workflow.steps.util.database.CheckIsDown',
            )}, {
            'Check patch if rollback': (
                ) + self.get_change_binaries_upgrade_patch_steps_rollback() + (
            )}, {
            'Configure if rollback': (
                'workflow.steps.util.plan.ConfigureLogRollback',
                'workflow.steps.util.plan.ConfigureRollback',
            )}, {
            'Remove previous VM': (
                'workflow.steps.util.volume_provider.DetachDataVolume',
                'workflow.steps.util.vm.WaitingBeReadyRollback',
                ('workflow.steps.util.host_provider.'
                 'DestroyVirtualMachineMigrateKeepObject')
            )}, {
            'Create new VM': (
                ('workflow.steps.util.host_provider.'
                 'RecreateVirtualMachineMigrate'),
            )}, {
            'Configure instance': (
                'workflow.steps.util.volume_provider.MoveDisk',
                'workflow.steps.util.volume_provider.AttachDataVolumeWithUndo',
                'workflow.steps.util.volume_provider.MountDataVolumeWithUndo',
                'workflow.steps.util.plan.Configure',
                'workflow.steps.util.plan.ConfigureLog',
            )}, {
            'Check patch': (
                ) + self.get_change_binaries_upgrade_patch_steps() + (
            )}, {
            'Starting database': (
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.database.StartRsyslog',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
                'workflow.steps.util.metric_collector.RestartTelegraf',
            )}, {
            'Enabling monitoring and alarms': (
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
            )}
        ]


class MySQLFoxHAGCP(MySQLFoxHA):
    def get_upgrade_steps_extra(self):
        return (
            'workflow.steps.util.volume_provider.AttachDataVolume',
            'workflow.steps.util.volume_provider.MountDataVolume',
            'workflow.steps.util.plan.InitializationForUpgrade',
            'workflow.steps.util.plan.ConfigureForUpgrade',
            'workflow.steps.util.plan.ConfigureLog',
            'workflow.steps.util.metric_collector.ConfigureTelegraf',
            'workflow.steps.util.vm.CheckHostName',
            'workflow.steps.util.mysql.SetFilePermission',
            'workflow.steps.util.plan.Configure',
            'workflow.steps.util.plan.ConfigureLog',
            'workflow.steps.util.mysql.SkipSlaveStart',
            'workflow.steps.util.mysql.DisableLogBin',
            'workflow.steps.util.database.Start',
            'workflow.steps.util.database.CheckIsUp',
            'workflow.steps.util.mysql.RunMySQLUpgrade',
            'workflow.steps.util.mysql.InstallAuditPlugin',
            'workflow.steps.util.mysql.CheckIfAuditPluginIsInstalled',
            'workflow.steps.util.database.Stop',
            'workflow.steps.util.plan.ConfigureForUpgrade',
            'workflow.steps.util.plan.ConfigureLog',
        )

    def get_upgrade_steps(self):
        return [{
            self.get_upgrade_steps_initial_description(): (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
            ),
        }] + [{
            self.get_upgrade_steps_description(): (
                'workflow.steps.util.database.checkAndFixMySQLReplication',
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.CheckIfSwitchMaster',
                'workflow.steps.util.database.Stop',
                'workflow.steps.util.database.StopRsyslog',
                'workflow.steps.util.database.CheckIsDown',
                'workflow.steps.util.host_provider.Stop',
                'workflow.steps.util.volume_provider.DetachDataVolume',
                'workflow.steps.util.host_provider.InstallNewTemplate',
                'workflow.steps.util.vip_provider.AddInstancesInGroup',
                'workflow.steps.util.host_provider.Start',
                'workflow.steps.util.vm.WaitingBeReady',
                'workflow.steps.util.vm.UpdateOSDescription',
                'workflow.steps.util.host_provider.UpdateHostRootVolumeSize',
            ) + self.get_upgrade_steps_extra() + (
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.StartSlave',
                'workflow.steps.util.metric_collector.RestartTelegraf',
            ),
        }] + self.get_upgrade_steps_final()

    def get_host_migrate_steps(self):
        return [{
            'Disable monitoring and alarms': (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
                'workflow.steps.util.fox.IsReplicationOkRollback',
                'workflow.steps.util.database.checkAndFixMySQLReplication',
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.CheckIfSwitchMaster',
                'workflow.steps.util.database.StopSlaveIfRunning',
            )}, {
            'Stop pevious database': (
                'workflow.steps.util.metric_collector.RestartTelegrafRollback',
                ('workflow.steps.util.metric_collector'
                 '.ConfigureTelegrafRollback'),
                'workflow.steps.util.database.CheckIsUpRollback',
                'workflow.steps.util.database.StopRsyslog',
            )}, {
            'Check patch if rollback': (
                ) + self.get_change_binaries_upgrade_patch_steps_rollback() + (
            )}, {
            'Reconfigure FOX if rollback': (
                ('workflow.steps.util.vip_provider.'
                 'DestroyEmptyInstanceGroupMigrateRollback'),
                ('workflow.steps.util.vip_provider.'
                 'UpdateBackendServiceMigrateRollback'),
                'workflow.steps.util.vip_provider.AddInstancesInGroupRollback',
                ('workflow.steps.util.vip_provider.'
                 'UpdateInstanceGroupRollback'),
            )}, {
            'Configure if rollback': (
                'workflow.steps.util.plan.ConfigureLogRollback',
                'workflow.steps.util.plan.ConfigureRollback',
                'workflow.steps.util.plan.InitializationMigrateRollback',
            )}, {
            'Remove previous VM': (
                'workflow.steps.util.volume_provider.DetachDataVolume',
                'workflow.steps.util.vm.WaitingBeReadyRollback',
                ('workflow.steps.util.host_provider.'
                 'DestroyVirtualMachineMigrateKeepObject')
            )}, {
            'Create new VM': (
                ('workflow.steps.util.host_provider.'
                 'RecreateVirtualMachineMigrate'),
            )}, {
            'Configure instance': (
                'workflow.steps.util.volume_provider.MoveDisk',
                'workflow.steps.util.volume_provider.AttachDataVolumeWithUndo',
                'workflow.steps.util.volume_provider.MountDataVolumeWithUndo',
                'workflow.steps.util.vm.WaitingBeReady',
                'workflow.steps.util.plan.InitializationMigrate',
                'workflow.steps.util.plan.Configure',
                'workflow.steps.util.plan.ConfigureLog',
                'workflow.steps.util.acl.ReplicateAclsMigrate',
            )}, {
            'Reconfigure FOX': (
                'workflow.steps.util.vip_provider.UpdateInstanceGroupWithoutRollback',
                'workflow.steps.util.vip_provider.AddInstancesInGroup',
                'workflow.steps.util.vip_provider.UpdateBackendServiceMigrate',
                ('workflow.steps.util.vip_provider.'
                 'DestroyEmptyInstanceGroupMigrate'),
            )}, {
            'Check patch': (
                ) + self.get_change_binaries_upgrade_patch_steps() + (
            )}, {
            'Starting database': (
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.database.StartSlave',
                'workflow.steps.util.fox.IsReplicationOk',
                'workflow.steps.util.database.StartRsyslog',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
                'workflow.steps.util.metric_collector.RestartTelegraf',
            )}, {
            'Enabling monitoring and alarms': (
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
            )}
        ]

    def get_migrate_engines_steps(self):
        return [{
            self.get_upgrade_steps_initial_description(): (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
            ),
        }] + [{
            self.get_upgrade_steps_description(): (
                ('workflow.steps.util.database.'
                 'checkAndFixMySQLReplicationIfRunning'),
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.CheckIfSwitchMaster',
                'workflow.steps.util.database.StopIfRunning',
                'workflow.steps.util.database.StopRsyslogIfRunning',
                'workflow.steps.util.database.CheckIsDown',
                'workflow.steps.util.host_provider.StopIfRunning',
                'workflow.steps.util.volume_provider.DetachDataVolume',
                ('workflow.steps.util.host_provider.'
                 'InstallMigrateEngineTemplate'),
                'workflow.steps.util.host_provider.Start',
                'workflow.steps.util.vm.WaitingBeReady',
                'workflow.steps.util.vm.UpdateOSDescription',
                'workflow.steps.util.vm.CheckHostName',
            ) + self.get_migrate_engine_steps_extra() + (
                'workflow.steps.util.vip_provider.AddInstancesInGroup',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.host_provider.UpdateHostRootVolumeSize',
                'workflow.steps.util.metric_collector.RestartTelegraf',
            ),
        }] + self.get_migrate_engine_steps_final()

    def get_recreate_slave_steps(self):
        return [{
            'Recreate Slave': (
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.CheckIfSwitchMaster',
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
                'workflow.steps.util.volume_provider.TakeSnapshotFromMaster',
                ('workflow.steps.util.volume_provider'
                    '.WaitSnapshotAvailableMigrate'),
                'workflow.steps.util.agents.Stop',
                'workflow.steps.util.database.StopSlaveIfRunning',
                'workflow.steps.util.database.StopIfRunning',
                'workflow.steps.util.database.StopRsyslog',
                'workflow.steps.util.database.CheckIsDown',
                'workflow.steps.util.volume_provider.NewVolumeFromMaster',
                'workflow.steps.util.volume_provider.AttachDataVolumeUpgradeDiskType',
                'workflow.steps.util.volume_provider.DetachFirstVolume',
                'workflow.steps.util.volume_provider.DestroyFirstVolume',
                'workflow.steps.util.volume_provider.MountDataVolumeUpgradeDiskType',
                'workflow.steps.util.volume_provider.RemoveSnapshotMigrate',
                'workflow.steps.util.disk.RemoveDeprecatedFiles',
                'workflow.steps.util.mysql.SetFilePermission',
                'workflow.steps.util.mysql.DisableReplicationRecreateSlave',
                'workflow.steps.util.database.Start',
                'workflow.steps.util.mysql.SetMasterRecreateSlave',
                'workflow.steps.util.mysql.EnableReplicationRecreateSlave',
                'workflow.steps.util.database.StartSlave',
                'workflow.steps.util.agents.Stop',
                'workflow.steps.util.agents.StartIgnoreRaise',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.fox.IsReplicationOk',
                'workflow.steps.util.metric_collector.RestartTelegraf',
                'workflow.steps.util.db_monitor.EnableMonitoring',
                'workflow.steps.util.zabbix.EnableAlarms',
                'workflow.steps.util.database.ConfigurePrometheusMonitoring'
                )
            }] + self.get_configure_db_params_steps()

    def get_reinstallvm_steps(self):
        return [{
            'Disable monitoring and alarms': (
                'workflow.steps.util.zabbix.DisableAlarms',
                'workflow.steps.util.db_monitor.DisableMonitoring',
            ),
        }] + [{
            'Reinstall VM': (
                ('workflow.steps.util.database.'
                 'checkAndFixMySQLReplicationIfRunning'),
                'workflow.steps.util.vm.ChangeMaster',
                'workflow.steps.util.database.StopIfRunning',
                'workflow.steps.util.database.StopRsyslogIfRunning',
                'workflow.steps.util.host_provider.StopIfRunning',
                'workflow.steps.util.volume_provider.DetachDataVolume',
                'workflow.steps.util.host_provider.ReinstallTemplate',
                'workflow.steps.util.host_provider.Start',
                'workflow.steps.util.vm.WaitingBeReady',
                'workflow.steps.util.vm.UpdateOSDescription',
                'workflow.steps.util.host_provider.UpdateHostRootVolumeSize',
            ),
        }] + [{
            'Start Database': (
                'workflow.steps.util.volume_provider.AttachDataVolume',
                'workflow.steps.util.volume_provider.MountDataVolume',
                'workflow.steps.util.vip_provider.AddInstancesInGroup',
                'workflow.steps.util.plan.Initialization',
                'workflow.steps.util.plan.Configure',
                'workflow.steps.util.plan.ConfigureLog',
                'workflow.steps.util.metric_collector.ConfigureTelegraf',
                'workflow.steps.util.database.Stop',
                ) + self.get_change_binaries_upgrade_patch_steps() + (
                'workflow.steps.util.database.Start',
                'workflow.steps.util.database.CheckIsUp',
                'workflow.steps.util.metric_collector.RestartTelegraf',
            ),
        }] + self.get_reinstallvm_steps_final() + self.get_configure_db_params_steps()
