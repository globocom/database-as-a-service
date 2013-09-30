# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import pymongo
from contextlib import contextmanager
from base.driver import BaseDriver, InstanceStatus, DatabaseStatus
    #AuthenticationError, ErrorRunningScript, ConnectionError
from pprint import pprint

LOG = logging.getLogger(__name__)


class MongoDB(BaseDriver):

    SCRIPT = "./MongoManager.sh"
    
    def get_connection(self):
        return u"%s:%s" % (self.instance.node.address, self.instance.node.port)

    @contextmanager
    def pymongo(self, database=None):
        try:
            client = pymongo.MongoClient(self.instance.node.address, int(self.instance.node.port))
            if database is None:
                return_value = client
            else:
                return_value = getattr(client, database.name)
            yield return_value
        finally:
            client.disconnect()

    def check_status(self):
        with self.pymongo() as client:
            LOG.debug("ping=", client.admin.command('ping'))

    def info(self):
        instance_status = InstanceStatus(instance_model=self.instance)

        with self.pymongo() as client:
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

        return instance_status

    def create_user(self, credential):
        with self.pymongo(credential.database) as mongo_database:
            mongo_database.add_user(credential.user, password=credential.password, read_only=False)

    def remove_user(self, credential):
        with self.pymongo(credential.database) as mongo_database:
            mongo_database.remove_user(credential.user)

    def create_database(self, database):
        with self.pymongo(database) as mongo_database:
            mongo_database.create_collection("teste-collection")
            mongo_database.drop_collection("teste-collection")

    def remove_database(self, database):
        with self.pymongo() as client:
            client.drop_database(database.name)

