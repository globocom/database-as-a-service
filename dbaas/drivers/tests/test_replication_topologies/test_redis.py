# -*- coding: utf-8 -*-
from __future__ import absolute_import
from drivers.replication_topologies.base import STOP_RESIZE_START
from drivers.replication_topologies.redis import RedisSentinel, RedisSingle, \
    RedisSingleNoPersistence, RedisSentinelNoPersistence
from drivers.tests.test_replication_topologies import AbstractReplicationTopologySettingsTestCase


class AbstractBaseRedisTestCase(AbstractReplicationTopologySettingsTestCase):

    def _get_deploy_first_settings(self):
        return (
            'workflow.steps.redis.deploy.build_databaseinfra.BuildDatabaseInfra',
            'workflow.steps.redis.deploy.create_virtualmachines.CreateVirtualMachine',
            'workflow.steps.redis.deploy.create_dns.CreateDns',
            'workflow.steps.util.deploy.create_nfs.CreateNfs',
            'workflow.steps.redis.deploy.init_database.InitDatabaseRedis',
            'workflow.steps.util.deploy.config_backup_log.ConfigBackupLog',
            'workflow.steps.util.deploy.check_database_connection.CheckDatabaseConnection',
            'workflow.steps.util.deploy.check_dns.CheckDns',
            'workflow.steps.util.deploy.start_monit.StartMonit',
        )

    def _get_deploy_last_settings(self):
        return (
            'workflow.steps.util.deploy.build_database.BuildDatabase',
            'workflow.steps.util.deploy.check_database_binds.CheckDatabaseBinds',
        )

    def _get_clone_settings(self):
        return self._get_deploy_first_settings() + self._get_deploy_last_settings() + (
            'workflow.steps.redis.clone.clone_database.CloneDatabase',
            'workflow.steps.util.resize.check_database_status.CheckDatabaseStatus',
        ) + self._get_monitoring_settings()

    def _get_resize_settings(self):
        return [{'Resizing database': ((
            'workflow.steps.util.zabbix.DisableAlarms',
            'workflow.steps.util.vm.ChangeMaster',
            'workflow.steps.util.database.Stop',
            'workflow.steps.util.pack.RedisWithPersistenceConfigure',
        ) + STOP_RESIZE_START + (
            'workflow.steps.util.database.Start',
            'workflow.steps.util.resize.start_agents.StartAgents',
            'workflow.steps.util.database.CheckIsUp',
            'workflow.steps.util.update_info.UpdateOffering',
            'workflow.steps.util.update_info.UpdateMemory',
            'workflow.steps.util.zabbix.EnableAlarms',
        ))}]


    def _get_upgrade_steps_extra(self):
        return (
            'workflow.steps.redis.upgrade.plan.InitializationRedis',
            'workflow.steps.redis.upgrade.plan.ConfigureRedis',
            'workflow.steps.redis.upgrade.pack.ConfigureRedis',
        )


class TestRedisSingle(AbstractBaseRedisTestCase):

    def _get_replication_topology_driver(self):
        return RedisSingle()


class TestRedisSentinel(AbstractBaseRedisTestCase):

    def _get_replication_topology_driver(self):
        return RedisSentinel()

    def _get_upgrade_steps_final(self):
        return [{
            'Resetting Sentinel': (
                'workflow.steps.redis.upgrade.sentinel.Reset',
            ),
        }] + super(TestRedisSentinel, self)._get_upgrade_steps_final()


class AbstractBaseRedisNoPersistenceTestCase(AbstractBaseRedisTestCase):
    def _get_resize_settings(self):
        return [{'Resizing database': ((
            'workflow.steps.util.zabbix.DisableAlarms',
            'workflow.steps.util.vm.ChangeMaster',
            'workflow.steps.util.database.Stop',
             'workflow.steps.util.pack.RedisWithoutPersistenceConfigure',
        ) + STOP_RESIZE_START + (
            'workflow.steps.util.database.Start',
            'workflow.steps.util.resize.start_agents.StartAgents',
            'workflow.steps.util.database.CheckIsUp',
            'workflow.steps.util.update_info.UpdateOffering',
            'workflow.steps.util.update_info.UpdateMemory',
            'workflow.steps.util.zabbix.EnableAlarms',
        ))}]


class TestRedisSingleNoPersistence(AbstractBaseRedisNoPersistenceTestCase):

    def _get_replication_topology_driver(self):
        return RedisSingleNoPersistence()


class TestRedisSentinelNoPersistence(AbstractBaseRedisNoPersistenceTestCase):

    def _get_replication_topology_driver(self):
        return RedisSentinelNoPersistence()

    def _get_upgrade_steps_final(self):
        return [{
            'Resetting Sentinel': (
                'workflow.steps.redis.upgrade.sentinel.Reset',
            ),
        }] + super(TestRedisSentinelNoPersistence, self)._get_upgrade_steps_final()
