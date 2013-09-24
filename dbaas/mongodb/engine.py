# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import collections
from base.engine import BaseEngine

LOG = logging.getLogger(__name__)


class MongoDB(BaseEngine):

    SCRIPT = "./MongoManager.sh"
    
    def get_connection(self):
        return u"%s:%s" % (self.instance.node.address, self.instance.node.port)

    def status(self):
        raise NotImplementedError()

    def create_user(self, credential):
        self.run_mongo("adduser", [credential, credential.database])

    def remove_user(self, credential):
        self.run_mongo("dropuser", [credential, credential.database])

    def create_database(self, database):
        self.run_mongo("createdatabase", [database])

    def remove_database(self, database):
        self.run_mongo("dropdatabase", [database])

    def list_databases(self):
        """list databases in a instance"""
        raise NotImplementedError()

    def run_mongo(self, operation, objects):
        envs = collections.OrderedDict()
        for obj in objects + [self.instance, self.instance.plan]:
            envs.update(self.to_envs(obj))
        # put plan attributes
        for plan_attribute in self.instance.plan.plan_attributes.all():
            envs['PLAN_ATTRIBUTE_%s' % plan_attribute.name.upper()] = plan_attribute.value
        self.call_script(MongoDB.SCRIPT, [operation], envs=envs)

