# -*- coding: utf-8 -*-
from base import BaseTopology

class MySQLFoxHA(BaseTopology):

    def get_deploy_steps(self):
        return (
            'workflow.steps.util.deploy.build_databaseinfra.BuildDatabaseInfra',
            'workflow.steps.mysql.deploy.create_virtualmachines.CreateVirtualMachine',
            'workflow.steps.mysql.deploy.create_vip.CreateVip',
            'workflow.steps.mysql.deploy.create_dns_foxha.CreateDnsFoxHA',
            'workflow.steps.util.deploy.create_nfs.CreateNfs',
            'workflow.steps.mysql.deploy.init_database_foxha.InitDatabaseFoxHA',
            'workflow.steps.mysql.deploy.check_pupet.CheckPuppetIsRunning',
            'workflow.steps.mysql.deploy.config_vms_foreman.ConfigVMsForeman',
            'workflow.steps.mysql.deploy.run_pupet_setup.RunPuppetSetup',
            'workflow.steps.mysql.deploy.config_fox.ConfigFox',
            'workflow.steps.util.deploy.config_backup_log.ConfigBackupLog',
            'workflow.steps.util.deploy.check_database_connection.CheckDatabaseConnection',
            'workflow.steps.util.deploy.check_dns.CheckDns',
            'workflow.steps.util.deploy.create_zabbix.CreateZabbix',
            'workflow.steps.util.deploy.start_monit.StartMonit',
            'workflow.steps.util.deploy.create_dbmonitor.CreateDbMonitor',
            'workflow.steps.util.deploy.build_database.BuildDatabase',
            'workflow.steps.util.deploy.create_log.CreateLog',
            'workflow.steps.util.deploy.check_database_binds.CheckDatabaseBinds',
        )
