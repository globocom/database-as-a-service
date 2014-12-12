# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import redis
from contextlib import contextmanager
from . import BaseDriver
from . import DatabaseInfraStatus
from . import DatabaseStatus
from . import ConnectionError
from system.models import Configuration
from workflow.settings import DEPLOY_REDIS
from workflow.settings import RESIZE_REDIS
from workflow.settings import CLONE_REDIS

LOG = logging.getLogger(__name__)

CLONE_DATABASE_SCRIPT_NAME="redis_clone.py"
REDIS_CONNECTION_DEFAULT_TIMEOUT=5

class Redis(BaseDriver):

    default_port = 6379
    DEPLOY = DEPLOY_REDIS
    CLONE = RESIZE_REDIS
    RESIZE = CLONE_REDIS

    def get_connection(self, database=None):
        uri = "redis://:<password>@%s/0" % (self.databaseinfra.endpoint)
        return uri

    def get_connection_dns(self, database=None):
        uri = "redis://:<password>@%s/0" % (self.databaseinfra.endpoint_dns)
        return uri

    def __get_admin_connection(self, instance=None):
        """
        endpoint is on the form HOST:PORT
        """
        if instance:
            return instance.address, instance.port

        endpoint = self.databaseinfra.endpoint.split(':')
        return endpoint[0], int(endpoint[1])

    def __redis_client__(self, instance):
        connection_address, connection_port = self.__get_admin_connection(instance)
        try:
            LOG.debug('Connecting to redis databaseinfra %s', self.databaseinfra)
            # redis uses timeout in seconds
            connection_timeout_in_seconds = Configuration.get_by_name_as_int('redis_connect_timeout', default=REDIS_CONNECTION_DEFAULT_TIMEOUT)

            client = redis.Redis(host = connection_address,
                                 port = int(connection_port),
                                 password = self.databaseinfra.password,
                                 socket_connect_timeout = connection_timeout_in_seconds)

            LOG.debug('Successfully connected to redis databaseinfra %s' % (self.databaseinfra))
            return client
        except Exception, e:
            raise e

    def get_client(self, instance):
        return self.__redis_client__(instance)

    def lock_database(self, client):
        pass

    def unlock_database(self, client):
        pass

    @contextmanager
    def redis(self, instance=None, database=None):
        client = None
        try:
            client = self.__redis_client__(instance)

            return_value = client
            yield return_value
        except Exception, e:
            raise ConnectionError('Error connecting to databaseinfra %s (%s): %s' %
                                 (self.databaseinfra, self.__get_admin_connection(), str(e)))

    def check_status(self, instance=None):
        with self.redis(instance=instance) as client:
            try:
                ok = client.ping()
                return True
            except Exception, e:
                raise ConnectionError('Error connection to databaseinfra %s: %s' % (self.databaseinfra, str(e)))

            if not ok:
                raise ConnectionError('Invalid status for ping command to databaseinfra %s' % self.databaseinfra)

    def list_databases(self, instance=None):
        dbs_names = []
        with self.redis(instance=instance) as client:
            try:
                keyspace = client.info('keyspace')
                if len(keyspace) == 0:
                    dbs_names.append('db0')
                else:
                    for db in keyspace:
                        dbs_names.append(db)
            except Exception, e:
                raise ConnectionError('Error connection to databaseinfra %s: %s' % (self.databaseinfra, str(e)))
        return dbs_names

    def info(self):
        databaseinfra_status = DatabaseInfraStatus(databaseinfra_model=self.databaseinfra)

        with self.redis() as client:
            json_server_info = client.info()

            databaseinfra_status.version = json_server_info.get('redis_version', None)
            databaseinfra_status.used_size_in_bytes = json_server_info.get('used_memory', 0)

            list_databases = self.list_databases()
            for database in self.databaseinfra.databases.all():
                database_name = database.name
                db_status = DatabaseStatus(database)
                #is_alive?
                try:
                    if self.check_status():
                        db_status.is_alive = True
                except:
                    pass

                databaseinfra_status.databases_status[database_name] = db_status

        return databaseinfra_status

    def create_user(self, credential, roles=["readWrite", "dbAdmin"]):
        pass

    def update_user(self, credential):
        pass

    def remove_user(self, credential):
        pass

    def create_database(self, database):
        pass

    def remove_database(self, database):
        pass

    def change_default_pwd(self, instance):
        pass

    def clone(self):
        return CLONE_DATABASE_SCRIPT_NAME

    def check_instance_is_eligible_for_backup(self, instance):
        return True

    def check_instance_is_master(self, instance):
        return True
