# -*- coding: utf-8 -*-
from workflow.steps.mongodb.plan import InitializationMongoHA, ConfigureMongoHA


class InitializationMongoHAForUpgrade(InitializationMongoHA):
    def __init__(self, instance):
        super(InitializationMongoHAForUpgrade, self).__init__(instance)
        self.get_equivalent_plan()


class ConfigureMongoHAForUpgrade(ConfigureMongoHA):
    def __init__(self, instance):
        super(ConfigureMongoHAForUpgrade, self).__init__(instance)
        self.get_equivalent_plan()
