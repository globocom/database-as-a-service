# -*- coding: utf-8 -*-
from time import sleep
from workflow.steps.util.database import DatabaseStep
from workflow.steps.redis.util import (
    reset_sentinel,
    change_slave_priority_instance,
    change_slave_priority_file
)


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

    @property
    def not_elegible_instance(self):
        return self.instance

    def do(self):
        self.driver.set_configuration(
            self.not_elegible_instance, self.priority_field, self.priority
        )

    def undo(self):
        self.priority = 100
        self.do()


class ChangeEligibleInstance(DatabaseStep):

    @property
    def target_instance(self):
        raise NotImplementedError

    @property
    def original_value(self):
        raise NotImplementedError

    @property
    def final_value(self):
        raise NotImplementedError

    @property
    def is_valid(self):
        return (
            self.target_instance.is_redis and
            not self.target_instance.read_only
        )

    def do(self):

        if not self.is_valid:
            return

        change_slave_priority_instance(
            self.target_instance,
            self.final_value
        )
        change_slave_priority_file(
            self.target_instance.hostname,
            self.original_value,
            self.final_value
        )

    def undo(self):
        if not self.is_valid:
            return

        change_slave_priority_instance(
            self.target_instance,
            self.original_value
        )
        change_slave_priority_file(
            self.target_instance.hostname,
            self.final_value,
            self.original_value
        )


class SetInstanceEligible(ChangeEligibleInstance):

    def __unicode__(self):
        return "Set instances eligible to be master..."

    @property
    def original_value(self):
        return 0

    @property
    def final_value(self):
        return 100

class SetInstanceNotEligible(ChangeEligibleInstance):

    def __unicode__(self):
        return "Set instances not eligible to be master..."

    @property
    def original_value(self):
        return 100

    @property
    def final_value(self):
        return 0



class SetFutureInstanceEligible(SetInstanceEligible):

    @property
    def target_instance(self):
        return self.instance.future_instance


class SetFutureInstanceNotEligible(SetInstanceNotEligible):

    @property
    def target_instance(self):
        return self.instance.future_instance


class SetSourceInstanceEligible(SetInstanceEligible):

    def __init__(self, instance):
        super(DatabaseStep, self).__init__(instance)
        self.instance.address = self.instance.hostname.address

    @property
    def target_instance(self):
        return self.instance


class SetSourceInstanceNotEligible(SetInstanceNotEligible):

    def __init__(self, instance):
        super(DatabaseStep, self).__init__(instance)
        self.instance.address = self.instance.hostname.address

    @property
    def target_instance(self):
        return self.instance
