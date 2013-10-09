# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import collections
from drivers import BaseDriver, ErrorRunningScript, ConnectionError, \
    AuthenticationError, InstanceStatus, DatabaseStatus
import json
# import pymongo.json_util

LOG = logging.getLogger(__name__)

def load_mongo_json(json_string):
    return json.loads(json_string)
    # return json.loads(json_string, object_hook=pymongo.json_util.object_hook)


class MongoDBScript(BaseDriver):

    SCRIPT = "./MongoManager.sh"
    
    def get_connection(self):
        return "%s:%s" % (self.instance.node.address, self.instance.node.port)

    def check_status(self):
        self.run_mongo("status")

    def info(self):
        instance_status = InstanceStatus(instance_model=self.instance)

        # gambiarra, precisa acertar isto!
        import pymongo
        from pprint import pprint
        client = pymongo.MongoClient(self.instance.node.address, int(self.instance.node.port))
        json_status = client.server_info()

        print "** GERAL"
        pprint(json_status)

        # stdout = unicode(self.run_mongo("serverstatus")).strip()
        # LOG.debug('Server status return:\n%s', stdout)
        # json_status = load_mongo_json(stdout)
        instance_status.version = json_status.get('version', None)


        # stdout = unicode(self.run_mongo("listdatabases")).strip()
        # LOG.debug('List Databases return:\n%s', stdout)
        # json_status = load_mongo_json(stdout)
        instance_status.size_in_bytes = json_status.get('fileSize', 0)

        for database in self.instance.databases.all():
            database_name = database.name
            db_json_status = getattr(client, database_name).command('dbStats')
            db_status = DatabaseStatus(database)
            pprint(db_json_status)
            db_status.size_in_bytes = db_json_status.get("fileSize")
            instance_status.databases_status[database_name] = db_status

        client.disconnect()

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
            return self.call_script(self.SCRIPT, [operation], envs=envs)
        except ErrorRunningScript, e:
            if "auth fails" in e.stdout:
                raise AuthenticationError(message="Invalid credentials to connect to instance %s" % self.get_connection())
            elif "couldn\'t connect" in e.stdout:
                raise ConnectionError(message="Error connecting to %s: %s" % (self.get_connection(), e.stdout))
            raise
