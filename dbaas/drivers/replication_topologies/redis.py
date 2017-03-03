# -*- coding: utf-8 -*-
from base import BaseTopology


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

    def get_upgrade_steps_extra(self):
        return (
            'workflow.steps.redis.upgrade.plan.InitializationRedis',
            'workflow.steps.redis.upgrade.plan.ConfigureRedis',
            'workflow.steps.redis.upgrade.pack.ConfigureRedis',
        )

    def get_resize_extra_steps(self):
        return super(BaseRedis, self).get_resize_extra_steps() + (
            'workflow.steps.util.update.Memory',
        )



class RedisSingle(BaseRedis):
    pass


class RedisSentinel(BaseRedis):

    def get_upgrade_steps_final(self):
        return [{
            'Resetting Sentinel': (
                'workflow.steps.redis.upgrade.sentinel.Reset',
            ),
        }] + super(RedisSentinel, self).get_upgrade_steps_final()


class RedisNoPersistence(BaseRedis):
    pass


class RedisSentinelNoPersistence(RedisNoPersistence):

    def get_upgrade_steps_final(self):
        return [{
            'Resetting Sentinel': (
                'workflow.steps.redis.upgrade.sentinel.Reset',
            ),
        }] + super(RedisSentinelNoPersistence, self).get_upgrade_steps_final()
