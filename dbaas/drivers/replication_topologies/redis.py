# -*- coding: utf-8 -*-
from base import BaseTopology, STOP_RESIZE_START


class BaseRedis(BaseTopology):
    def deploy_first_steps(self):
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

    def deploy_last_steps(self):
        return (
            'workflow.steps.util.deploy.build_database.BuildDatabase',
            'workflow.steps.util.deploy.check_database_binds.CheckDatabaseBinds',
        )

    def get_clone_steps(self):
        return self.deploy_first_steps() + self.deploy_last_steps() + (
            'workflow.steps.redis.clone.clone_database.CloneDatabase',
            'workflow.steps.util.resize.check_database_status.CheckDatabaseStatus',
        ) + self.monitoring_steps()

    def get_resize_steps(self):
        return (
            ('workflow.steps.util.resize.stop_database.StopDatabase',
             'workflow.steps.redis.resize.change_config.RedisWithPersistence',) +
            STOP_RESIZE_START +
            ('workflow.steps.util.resize.start_database.StartDatabase',
             'workflow.steps.util.resize.start_agents.StartAgents',
             'workflow.steps.util.resize.check_database_status.CheckDatabaseStatus',)
        )


class RedisSingle(BaseRedis):
    pass


class RedisSentinel(BaseRedis):
    pass


class RedisNoPersistence(BaseRedis):

    def get_resize_steps(self):
        return (
            ('workflow.steps.util.resize.stop_database.StopDatabase',
             'workflow.steps.redis.resize.change_config.RedisWithoutPersistence',) +
            STOP_RESIZE_START +
            ('workflow.steps.util.resize.start_database.StartDatabase',
             'workflow.steps.util.resize.start_agents.StartAgents',
             'workflow.steps.util.resize.check_database_status.CheckDatabaseStatus',)
        )


class RedisSingleNoPersistence(RedisNoPersistence):
    pass


class RedisSentinelNoPersistence(RedisNoPersistence):
    pass
