# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from django.test import TestCase
from workflow.settings import DEPLOY_MONGO
from workflow.settings import DEPLOY_MYSQL
from workflow.settings import DEPLOY_REDIS
from workflow.settings import CLONE_MONGO
from workflow.settings import CLONE_MYSQL
from workflow.settings import CLONE_REDIS
from workflow.settings import RESIZE_MONGO
from workflow.settings import RESIZE_MYSQL
from workflow.settings import RESIZE_REDIS

LOG = logging.getLogger(__name__)


class WorkflowSettingsTestCase(TestCase):

    def test_deploy_settings(self):
        self.assertEqual(DEPLOY_MONGO, (
            'workflow.steps.util.deploy.build_databaseinfra.BuildDatabaseInfra',
            'workflow.steps.mongodb.deploy.create_virtualmachines.CreateVirtualMachine',
            'workflow.steps.util.deploy.create_dns.CreateDns',
            'workflow.steps.mongodb.deploy.create_nfs.CreateNfs',
            'workflow.steps.mongodb.deploy.init_database.InitDatabaseMongoDB',
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
        )

        self.assertEqual(DEPLOY_MYSQL, (
            'workflow.steps.util.deploy.build_databaseinfra.BuildDatabaseInfra',
            'workflow.steps.mysql.deploy.create_virtualmachines.CreateVirtualMachine',
            'workflow.steps.mysql.deploy.create_secondary_ip.CreateSecondaryIp',
            'workflow.steps.mysql.deploy.create_dns.CreateDns',
            'workflow.steps.util.deploy.create_nfs.CreateNfs',
            'workflow.steps.mysql.deploy.create_flipper.CreateFlipper',
            'workflow.steps.mysql.deploy.init_database.InitDatabase',
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
        )

        self.assertEqual(DEPLOY_REDIS, (
            'workflow.steps.redis.deploy.build_databaseinfra.BuildDatabaseInfra',
            'workflow.steps.redis.deploy.create_virtualmachines.CreateVirtualMachine',
            'workflow.steps.redis.deploy.create_dns.CreateDns',
            'workflow.steps.redis.deploy.create_nfs.CreateNfs',
            'workflow.steps.redis.deploy.init_database.InitDatabaseRedis',
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
        )

    def test_clone_settings(self):
        self.assertEqual(CLONE_MONGO, ('workflow.steps.util.deploy.build_databaseinfra.BuildDatabaseInfra',
                                       'workflow.steps.mongodb.deploy.create_virtualmachines.CreateVirtualMachine',
                                       'workflow.steps.util.deploy.create_dns.CreateDns',
                                       'workflow.steps.mongodb.deploy.create_nfs.CreateNfs',
                                       'workflow.steps.mongodb.deploy.init_database.InitDatabaseMongoDB',
                                       'workflow.steps.util.deploy.config_backup_log.ConfigBackupLog',
                                       'workflow.steps.util.deploy.check_database_connection.CheckDatabaseConnection',
                                       'workflow.steps.util.deploy.check_dns.CheckDns',
                                       'workflow.steps.util.deploy.create_zabbix.CreateZabbix',
                                       'workflow.steps.util.deploy.start_monit.StartMonit',
                                       'workflow.steps.util.deploy.create_dbmonitor.CreateDbMonitor',
                                       'workflow.steps.util.deploy.build_database.BuildDatabase',
                                       'workflow.steps.util.deploy.create_log.CreateLog',
                                       'workflow.steps.util.deploy.check_database_binds.CheckDatabaseBinds',
                                       'workflow.steps.util.clone.clone_database.CloneDatabase',
                                       'workflow.steps.util.resize.check_database_status.CheckDatabaseStatus',
                                       )
                         )

        self.assertEqual(CLONE_MYSQL, ('workflow.steps.util.deploy.build_databaseinfra.BuildDatabaseInfra',
                                       'workflow.steps.mysql.deploy.create_virtualmachines.CreateVirtualMachine',
                                       'workflow.steps.mysql.deploy.create_secondary_ip.CreateSecondaryIp',
                                       'workflow.steps.mysql.deploy.create_dns.CreateDns',
                                       'workflow.steps.util.deploy.create_nfs.CreateNfs',
                                       'workflow.steps.mysql.deploy.create_flipper.CreateFlipper',
                                       'workflow.steps.mysql.deploy.init_database.InitDatabase',
                                       'workflow.steps.util.deploy.config_backup_log.ConfigBackupLog',
                                       'workflow.steps.util.deploy.check_database_connection.CheckDatabaseConnection',
                                       'workflow.steps.util.deploy.check_dns.CheckDns',
                                       'workflow.steps.util.deploy.create_zabbix.CreateZabbix',
                                       'workflow.steps.util.deploy.start_monit.StartMonit',
                                       'workflow.steps.util.deploy.create_dbmonitor.CreateDbMonitor',
                                       'workflow.steps.util.deploy.build_database.BuildDatabase',
                                       'workflow.steps.util.deploy.create_log.CreateLog',
                                       'workflow.steps.util.deploy.check_database_binds.CheckDatabaseBinds',
                                       'workflow.steps.util.clone.clone_database.CloneDatabase',
                                       'workflow.steps.util.resize.check_database_status.CheckDatabaseStatus',
                                       )
                         )

        self.assertEqual(CLONE_REDIS, ('workflow.steps.redis.deploy.build_databaseinfra.BuildDatabaseInfra',
                                       'workflow.steps.redis.deploy.create_virtualmachines.CreateVirtualMachine',
                                       'workflow.steps.redis.deploy.create_dns.CreateDns',
                                       'workflow.steps.redis.deploy.create_nfs.CreateNfs',
                                       'workflow.steps.redis.deploy.init_database.InitDatabaseRedis',
                                       'workflow.steps.util.deploy.config_backup_log.ConfigBackupLog',
                                       'workflow.steps.util.deploy.check_database_connection.CheckDatabaseConnection',
                                       'workflow.steps.util.deploy.check_dns.CheckDns',
                                       'workflow.steps.util.deploy.create_zabbix.CreateZabbix',
                                       'workflow.steps.util.deploy.start_monit.StartMonit',
                                       'workflow.steps.util.deploy.create_dbmonitor.CreateDbMonitor',
                                       'workflow.steps.util.deploy.build_database.BuildDatabase',
                                       'workflow.steps.util.deploy.create_log.CreateLog',
                                       'workflow.steps.util.deploy.check_database_binds.CheckDatabaseBinds',
                                       'workflow.steps.redis.clone.clone_database.CloneDatabase',
                                       'workflow.steps.util.resize.check_database_status.CheckDatabaseStatus',
                                       ))

    def test_resize_settings(self):
        self.assertEqual(RESIZE_MONGO, ('workflow.steps.util.volume_migration.stop_database.StopDatabase',
                                        'workflow.steps.util.resize.stop_vm.StopVM',
                                        'workflow.steps.util.resize.resize_vm.ResizeVM',
                                        'workflow.steps.util.resize.start_vm.StartVM',
                                        'workflow.steps.util.resize.start_database.StartDatabase',
                                        'workflow.steps.util.resize.start_agents.StartAgents',
                                        'workflow.steps.util.resize.check_database_status.CheckDatabaseStatus',
                                        )
                         )

        self.assertEqual(RESIZE_MYSQL, ('workflow.steps.util.volume_migration.stop_database.StopDatabase',
                                        'workflow.steps.mysql.resize.change_config.ChangeDatabaseConfigFile',
                                        'workflow.steps.util.resize.stop_vm.StopVM',
                                        'workflow.steps.util.resize.resize_vm.ResizeVM',
                                        'workflow.steps.util.resize.start_vm.StartVM',
                                        'workflow.steps.util.resize.start_database.StartDatabase',
                                        'workflow.steps.util.resize.start_agents.StartAgents',
                                        'workflow.steps.util.resize.check_database_status.CheckDatabaseStatus',
                                        )
                         )

        self.assertEqual(RESIZE_REDIS, ('workflow.steps.util.volume_migration.stop_database.StopDatabase',
                                        'workflow.steps.redis.resize.change_config.ChangeDatabaseConfigFile',
                                        'workflow.steps.util.resize.stop_vm.StopVM',
                                        'workflow.steps.util.resize.resize_vm.ResizeVM',
                                        'workflow.steps.util.resize.start_vm.StartVM',
                                        'workflow.steps.util.resize.start_database.StartDatabase',
                                        'workflow.steps.util.resize.start_agents.StartAgents',
                                        'workflow.steps.util.resize.check_database_status.CheckDatabaseStatus',
                                        )
                         )
