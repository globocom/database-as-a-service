# -*- coding: utf-8 -*-
from workflow.steps.util.upgrade.plan import Initialization, Configure


def redis_instance_parameter(host):
    redis = host.database_instance()
    redis_address = ''
    redis_port = ''
    only_sentinel = True
    if redis:
        redis_address = redis.address
        redis_port = redis.port
        only_sentinel = False

    return {
        'HOSTADDRESS': redis_address,
        'PORT': redis_port,
        'ONLY_SENTINEL': only_sentinel,
    }


def sentinel_instance_parameter(host):
    sentinel = host.non_database_instance()
    sentinel_address = ''
    sentinel_port = ''
    if sentinel:
        sentinel_address = sentinel.address
        sentinel_port = sentinel.port

    return {
        'SENTINELADDRESS': sentinel_address,
        'SENTINELPORT': sentinel_port,
    }


class InitializationRedis(Initialization):

    def get_variables_specifics(self):
        return redis_instance_parameter(self.host)


class ConfigureRedis(Configure):

    def get_variables_specifics(self):
        master = self.instance.databaseinfra.get_driver().get_master_instance()

        variables = {
            'SENTINELMASTER': master.address,
            'SENTINELMASTERPORT': master.port,
            'MASTERNAME': self.instance.databaseinfra.name,
        }
        variables.update(redis_instance_parameter(self.host))
        variables.update(sentinel_instance_parameter(self.host))

        return variables
