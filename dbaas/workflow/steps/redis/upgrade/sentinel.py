# -*- coding: utf-8 -*-
from time import sleep
from workflow.steps.util.base import BaseInstanceStep
from workflow.steps.redis.util import reset_sentinel


class Reset(BaseInstanceStep):

    def __unicode__(self):
        return "Resetting Sentinel..."

    @property
    def sentinel_instance(self):
        self.host.non_database_instance()

    def do(self):
        sleep(10)
        if self.sentinel_instance:
            reset_sentinel(
                self.host,
                self.sentinel_instance.address,
                self.sentinel_instance.port,
                self.sentinel_instance.databaseinfra.name
            )

    def undo(self):
        pass


class ResetAllSentinel(BaseInstanceStep):

    def __unicode__(self):
        return "Resetting Sentinel..."

    def reset_sentinels(self):
        driver = self.infra.get_driver()
        for sentinel_instance in driver.get_non_database_instances():
            reset_sentinel(
                sentinel_instance.hostname,
                sentinel_instance.address,
                sentinel_instance.port,
                self.infra.name
            )

    def do(self):
        self.reset_sentinels()

    def undo(self):
        pass


class ResetAllSentinelRolllback(ResetAllSentinel):

    def do(self):
        pass

    def undo(self):
        self.reset_sentinels()
