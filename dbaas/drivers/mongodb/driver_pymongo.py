# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import pymongo
from contextlib import contextmanager
from .. import BaseDriver, InstanceStatus, DatabaseStatus, \
    AuthenticationError, ConnectionError
from django.contrib.auth.models import User

LOG = logging.getLogger(__name__)


class MongoDB(BaseDriver):

    default_port = 27017

    def get_connection(self):
        return "%s:%s" % (self.instance.node.address, self.instance.node.port)

    def __mongo_client__(self, node):
        client = pymongo.MongoClient(node.address, int(node.port))
        if self.instance.user and self.instance.password:
            LOG.debug('Authenticating instance %s', self.instance)
            client.admin.authenticate(self.instance.user, self.instance.password)
        return client

    @contextmanager
    def pymongo(self, node=None, database=None):
        client = None
        try:
            node = node or self.instance.node
            client = self.__mongo_client__(node)

            if database is None:
                return_value = client
            else:
                return_value = getattr(client, database.name)
            yield return_value
        except pymongo.errors.OperationFailure, e:
            if e.code == 18:
                raise AuthenticationError('Invalid credentials to instance %s' % self.instance)
            raise ConnectionError('Error connecting to instance %s: %s' % (self.instance, e.message))
        except pymongo.errors.PyMongoError, e:
            raise ConnectionError('Error connecting to instance %s: %s' % (self.instance, e.message))
        finally:
            try:
                if client:
                    client.disconnect()
            except:
                LOG.warn('Error disconnecting from instance %s. Ignoring...', self.instance, exc_info=True)

    def check_status(self, node=None):
        with self.pymongo(node=node) as client:
            try:
                ok = client.admin.command('ping')
            except pymongo.errors.PyMongoError, e:
                raise ConnectionError('Error connection to instance %s: %s' % (self.instance, e.message))

            if isinstance(ok, dict) and ok.get('ok', 0) != 1.0:
                raise ConnectionError('Invalid status for ping command to instance %s' % self.instance)

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
                if json_db_status.get('empty', False):
                    db_status.size_in_bytes = 0
                else:
                    db_status.size_in_bytes = json_db_status.get("sizeOnDisk") or 0
                instance_status.databases_status[database_name] = db_status

        return instance_status

    def create_user(self, credential):
        with self.pymongo(database=credential.database) as mongo_database:
            mongo_database.add_user(credential.user, password=credential.password, roles=["readWrite", "dbAdmin"])

    def remove_user(self, credential):
        with self.pymongo(database=credential.database) as mongo_database:
            mongo_database.remove_user(credential.user)

    def create_database(self, database):
        with self.pymongo(database=database) as mongo_database:
            mongo_database.collection_names()

    def remove_database(self, database):
        with self.pymongo() as client:
            client.drop_database(database.name)

    def change_default_pwd(self, node):
        with self.pymongo(node=node) as client:
            new_password = User.objects.make_random_password()
            client.admin.add_user(name=node.instance.user, password=new_password)
            return new_password
