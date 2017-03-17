# -*- coding: utf-8 -*-
from workflow.steps.util.plan import Initialization, Configure


class InitializationForUpgrade(Initialization):
    def __init__(self, instance):
        super(InitializationForUpgrade, self).__init__(instance)
        self.get_equivalent_plan()


class ConfigureForUpgrade(Configure):
    def __init__(self, instance):
        super(ConfigureForUpgrade, self).__init__(instance)
        self.get_equivalent_plan()
