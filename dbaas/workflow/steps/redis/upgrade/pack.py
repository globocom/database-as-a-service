# -*- coding: utf-8 -*-
from workflow.steps.util.upgrade.pack import Configure


class ConfigureRedis(Configure):

    def get_variables_specifics(self):
        redis = self.host.database_instance()
        redis_address = ''
        redis_port = ''
        if redis:
            redis_address = redis.address
            redis_port = redis.port

        return {
            'HOSTADDRESS': redis_address,
            'PORT': redis_port,
        }
