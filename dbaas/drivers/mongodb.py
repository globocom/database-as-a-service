# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import pymongo
from contextlib import contextmanager
from . import BaseDriver, DatabaseInfraStatus, DatabaseStatus, \
    AuthenticationError, ConnectionError
from util import make_db_random_password

LOG = logging.getLogger(__name__)


class MongoDB(BaseDriver):

    default_port = 27017

    def get_connection(self):
        return "mongodb://<user>:<password>@%s" % ",".join([ "%s:%s" % (instance.address, instance.port) for instance in self.databaseinfra.instances.filter(is_arbiter=False, is_active=True).all() ])

    def __mongo_client__(self, instance):
        try:
            client = pymongo.MongoClient(instance.address, int(instance.port))
            if self.databaseinfra.user and self.databaseinfra.password:
                LOG.debug('Authenticating databaseinfra %s', self.databaseinfra)
                client.admin.authenticate(self.databaseinfra.user, self.databaseinfra.password)
            return client
        except TypeError:
            raise AuthenticationError(message='Invalid address %s:%s' % (instance.address, instance.port))

    @contextmanager
    def pymongo(self, instance=None, database=None):
        client = None
        try:
            instance = instance or self.databaseinfra.instance
            client = self.__mongo_client__(instance)

            if database is None:
                return_value = client
            else:
                return_value = getattr(client, database.name)
            yield return_value
        except pymongo.errors.OperationFailure, e:
            if e.code == 18:
                raise AuthenticationError('Invalid credentials to databaseinfra %s' % self.databaseinfra)
            raise ConnectionError('Error connecting to databaseinfra %s: %s' % (self.databaseinfra, e.message))
        except pymongo.errors.PyMongoError, e:
            raise ConnectionError('Error connecting to databaseinfra %s: %s' % (self.databaseinfra, e.message))
        finally:
            try:
                if client:
                    client.disconnect()
            except:
                LOG.warn('Error disconnecting from databaseinfra %s. Ignoring...', self.databaseinfra, exc_info=True)

    def check_status(self, instance=None):
        with self.pymongo(instance=instance) as client:
            try:
                ok = client.admin.command('ping')
            except pymongo.errors.PyMongoError, e:
                raise ConnectionError('Error connection to databaseinfra %s: %s' % (self.databaseinfra, e.message))

            if isinstance(ok, dict) and ok.get('ok', 0) != 1.0:
                raise ConnectionError('Invalid status for ping command to databaseinfra %s' % self.databaseinfra)

    def info(self):
        databaseinfra_status = DatabaseInfraStatus(databaseinfra_model=self.databaseinfra)

        with self.pymongo() as client:
            json_server_info = client.server_info()
            json_list_databases = client.admin.command('listDatabases')

            databaseinfra_status.version = json_server_info.get('version', None)
            databaseinfra_status.used_size_in_bytes = json_list_databases.get('totalSize', 0)

            for database in self.databaseinfra.databases.all():
                database_name = database.name
                json_db_status = getattr(client, database_name).command('dbStats')
                db_status = DatabaseStatus(database)
                dataSize = json_db_status.get("dataSize") or 0
                indexSize = json_db_status.get("indexSize") or 0
                db_status.used_size_in_bytes = dataSize + indexSize
                db_status.total_size_in_bytes = json_db_status.get("fileSize") or 0
                databaseinfra_status.databases_status[database_name] = db_status

        return databaseinfra_status

    def create_user(self, credential, roles=["readWrite", "dbAdmin"]):
        with self.pymongo(database=credential.database) as mongo_database:
            mongo_database.add_user(credential.user, password=credential.password, roles=roles)

    def update_user(self, credential):
        self.create_user(credential)

    def remove_user(self, credential):
        with self.pymongo(database=credential.database) as mongo_database:
            mongo_database.remove_user(credential.user)

    def create_database(self, database):
        LOG.info("creating database %s" % database.name)
        with self.pymongo(database=database) as mongo_database:
            mongo_database.collection_names()

    def remove_database(self, database):
        LOG.info("removing database %s" % database.name)
        with self.pymongo() as client:
            client.drop_database(database.name)

    def change_default_pwd(self, instance):
        with self.pymongo(instance=instance) as client:
            new_password = make_db_random_password()
            client.admin.add_user(name=instance.databaseinfra.user, password=new_password)
            return new_password
