# -*- coding: utf-8 -*-
from workflow.steps.redis.plan import InitializationRedis, ConfigureRedis


class InitializationRedisForUpgrade(InitializationRedis):
    def __init__(self, instance):
        super(InitializationRedisForUpgrade, self).__init__(instance)
        self.get_equivalent_plan()


class ConfigureRedisForUpgrade(ConfigureRedis):
    def __init__(self, instance):
        super(ConfigureRedisForUpgrade, self).__init__(instance)
        self.get_equivalent_plan()
