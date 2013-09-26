# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import collections
from base.driver import BaseDriver, ErrorRunningScript, ConnectionError, \
    AuthenticationError, InstanceStatus, DatabaseStatus
import json

LOG = logging.getLogger(__name__)


class MongoDB(BaseDriver):

    SCRIPT = "./MongoManager.sh"
    
    def get_connection(self):
        return u"%s:%s" % (self.instance.node.address, self.instance.node.port)

    def check_status(self):
        self.run_mongo("status")

    def info(self):
        instance_status = InstanceStatus(instance_model=self.instance)

        stdout = unicode(self.run_mongo("serverstatus")).strip()
        json_status = json.loads(stdout)
        instance_status.version = json_status.get('version', None)

        stdout = unicode(self.run_mongo("listdatabases")).strip()
        json_status = json.loads(stdout)
        instance_status.size_in_bytes = json_status.get('totalSize', None)

        for database in json_status.get("databases", []):
            database_name = database["name"]
            db_status = DatabaseStatus(self.instance.databases.get(name=database_name))
            db_status.size_in_bytes = database.get("sizeOnDisk")
            instance_status.databases_status[database_name] = db_status

        return instance_status

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

    def run_mongo(self, operation, objects=[]):
        envs = collections.OrderedDict()
        for obj in objects + [self.instance, self.instance.plan]:
            envs.update(self.to_envs(obj))
        # put plan attributes
        for plan_attribute in self.instance.plan.plan_attributes.all():
            envs['PLAN_ATTRIBUTE_%s' % plan_attribute.name.upper()] = plan_attribute.value

        try:
            return self.call_script(MongoDB.SCRIPT, [operation], envs=envs)
        except ErrorRunningScript, e:
            if "auth fails" in e.stdout:
                raise AuthenticationError(message="Invalid credentials to connect to instance %s" % self.get_connection())
            elif "couldn\'t connect" in e.stdout:
                raise ConnectionError(message="Error connecting to %s: %s" % (self.get_connection(), e.stdout))
            raise
