# -*- coding: utf-8 -*-
from time import sleep
from workflow.steps.util.database import DatabaseStep
from workflow.steps.redis.util import reset_sentinel


class AddInstanceToRedisCluster(DatabaseStep):

    def __unicode__(self):
        return "Adding instance to Redis Cluster..."

    def do(self):
        master = self.driver.get_master_instance()
        client = self.driver.get_client(self.instance)
        client.slaveof(master.address, master.port)

    def undo(self):
        self.stop_database()
        sleep(10)

        sentinel_instances = self.driver.get_non_database_instances()
        for sentinel_instance in sentinel_instances:
            host = sentinel_instance.hostname
            reset_sentinel(
                host,
                sentinel_instance.address,
                sentinel_instance.port,
                self.infra.name
            )

        sleep(10)
        self.start_database()


class SetNotEligible(DatabaseStep):

    def __unicode__(self):
        return "Set instance not eligible to be master..."

    def __init__(self, instance):
        super(SetNotEligible, self).__init__(instance)
        self.priority = 0

    @property
    def priority_field(self):
        return "slave-priority"

    def do(self):
        self.driver.set_configuration(
            self.instance, self.priority_field, self.priority
        )

    def undo(self):
        self.priority = 100
        self.do()
