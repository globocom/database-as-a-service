# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import pymongo
from contextlib import contextmanager
from base.driver import BaseDriver, InstanceStatus, DatabaseStatus
    #AuthenticationError, ErrorRunningScript, ConnectionError

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
            json_server_info = client.server_info()
            json_list_databases = client.admin.command('listDatabases')

            instance_status.version = json_server_info.get('version', None)
            instance_status.size_in_bytes = json_list_databases.get('totalSize', 0)

            json_databases = dict([(json_db['name'], json_db) for json_db in json_list_databases.get('databases', [])])

            for database in self.instance.databases.all():
                database_name = database.name
                json_db_status = json_databases.get(database_name, {})
                db_status = DatabaseStatus(database)
                db_status.size_in_bytes = json_db_status.get("sizeOnDisk") or 0
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

