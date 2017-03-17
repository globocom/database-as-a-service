# -*- coding: utf-8 -*-
from workflow.steps.util.plan import Initialization, Configure


class InitializationMongoHA(Initialization):

    def get_variables_specifics(self):
        database_rule = 'SECONDARY'
        if self.instance.instance_type == self.instance.MONGODB_ARBITER:
            database_rule = 'ARBITER'

        return {
            'DATABASERULE': database_rule
        }


class ConfigureMongoHA(Configure):

    def get_variables_specifics(self):
        return {
            'REPLICASETNAME': self.instance.databaseinfra.get_driver().replica_set_name,
            'MONGODBKEY': self.instance.databaseinfra.database_key
        }
