# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import _mysql as mysqldb
import _mysql_exceptions
from contextlib import contextmanager
from . import BaseDriver, DatabaseInfraStatus, AuthenticationError, ConnectionError, GenericDriverError, \
    DatabaseAlreadyExists, InvalidCredential, DatabaseStatus, DatabaseDoesNotExist
from util import make_db_random_password
from system.models import Configuration

LOG = logging.getLogger(__name__)

ER_DB_CREATE_EXISTS = 1007
ER_DB_DROP_EXISTS = 1008
ER_ACCESS_DENIED_ERROR = 1045
ER_CANNOT_USER = 1396
ER_WRONG_STRING_LENGTH = 1470
ER_CAN_NOT_CONNECT = 2003

# mysql uses timeout in seconds
MYSQL_CONNECT_TIMEOUT = Configuration.get_by_name('MYSQL_CONNECT_TIMEOUT') or 5


class MySQL(BaseDriver):

    default_port = 3306

    def get_connection(self):
        my_instance = self.databaseinfra.instances.all()[0]
        return "mysql://<user>:<password>@%s" % (my_instance.address)

    def __get_admin_connection(self, instance=None):
        if instance:
            return instance.address, instance.port
        my_instance = self.databaseinfra.instances.all()[0]
        return my_instance.address, my_instance.port

    def __mysql_client__(self, instance, database='mysql'):
        connection_address, connection_port = self.__get_admin_connection(instance)
        try:
            LOG.debug('Connecting to mysql databaseinfra %s', self.databaseinfra)
            client = mysqldb.connect(host=connection_address, port=int(connection_port),
                                     user=self.databaseinfra.user, passwd=self.databaseinfra.password,
                                     db=database, connect_timeout=MYSQL_CONNECT_TIMEOUT)
            LOG.debug('Successfully connected to mysql databaseinfra %s', self.databaseinfra)
            return client
        except Exception, e:
            raise e

    @contextmanager
    def mysqldb(self, instance=None, database=None):
        client = None
        try:
            yield self.__mysql_client__(instance)
        except _mysql_exceptions.OperationalError, e:
            if e.args[0] == ER_ACCESS_DENIED_ERROR:
                raise AuthenticationError(e.args[1])
            elif e.args[0] == ER_CAN_NOT_CONNECT:
                raise ConnectionError(e.args[1])
            else:
                raise GenericDriverError(e.args)
        finally:
            try:
                if client:
                    LOG.debug('Disconnecting mysql databaseinfra %s', self.databaseinfra)
                    client.close()
            except:
                LOG.warn('Error disconnecting from databaseinfra %s. Ignoring...', self.databaseinfra, exc_info=True)

    def __query(self, query_string, instance=None):
        with self.mysqldb(instance=instance) as client:
            try:
                client.query(query_string)
                r = client.store_result()
                if r is not None:
                    return r.fetch_row(maxrows=0, how=1)
            except _mysql_exceptions.ProgrammingError, e:
                if e.args[0] == ER_DB_CREATE_EXISTS:
                    raise DatabaseAlreadyExists(e.args[1])
                else:
                    raise GenericDriverError(e.args)
            except _mysql_exceptions.OperationalError, e:
                if e.args[0] == ER_DB_DROP_EXISTS:
                    raise DatabaseDoesNotExist(e.args[1])
                elif e.args[0] == ER_CANNOT_USER:
                    raise InvalidCredential(e.args[1])
                elif e.args[0] == ER_WRONG_STRING_LENGTH:
                    raise InvalidCredential(e.args[1])
                else:
                    raise GenericDriverError(e.args)
            except Exception, e:
                GenericDriverError(e.args)

    def info(self):
        databaseinfra_status = DatabaseInfraStatus(databaseinfra_model=self.databaseinfra)

        r = self.__query("SELECT VERSION()")
        databaseinfra_status.version = r[0]['VERSION()']
        my_all_dbs = self.__query("SHOW DATABASES")
        db_sizes = self.__query("SELECT table_schema 'Database', SUM( data_length + index_length) 'Size' \
                                    FROM information_schema.TABLES GROUP BY table_schema")

        all_dbs = {}
        for database in db_sizes:
            all_dbs[database['Database']] = int(database['Size'])

        for database in my_all_dbs:
            db_status = DatabaseStatus(database)
            db_status.total_size_in_bytes = 0
            if database['Database'] in all_dbs:
                db_status.used_size_in_bytes = all_dbs[database['Database']]
            else:
                db_status.used_size_in_bytes = 0
            databaseinfra_status.databases_status[database['Database']] = db_status
        databaseinfra_status.used_size_in_bytes = sum(all_dbs.values())

        return databaseinfra_status

    def check_status(self, instance=None):
        self.__query("SELECT 1", instance=instance)

    def create_database(self, database):
        LOG.info("creating database %s" % database.name)
        self.__query("CREATE DATABASE %s" % database.name)

    def create_user(self, credential, roles=["ALL PRIVILEGES"]):
        LOG.info("creating user %s to %s" % (credential.user, credential.database))
        # the first release allow every host to connect to the database
        # 2 steps required to get the user create error
        self.__query("CREATE USER '%s'@'%%' IDENTIFIED BY '%s'" % (credential.user, credential.password))
        self.__query("GRANT %s ON %s.* TO '%s'@'%%'" % (','.join(roles), credential.database, credential.user))

    def remove_database(self, database):
        LOG.info("removing database %s" % database.name)
        self.__query("DROP DATABASE %s" % database.name)

    def remove_user(self, credential):
        LOG.info("removing user %s from %s" % (credential.user, credential.database))
        self.__query("DROP USER '%s'@'%%'" % credential.user)

    def update_user(self, credential):
        self.remove_user(credential)
        self.create_user(credential)

    def change_default_pwd(self, instance):
        new_password = make_db_random_password()
        self.__query("SET PASSWORD FOR '%s'@'%%' = PASSWORD('%s')" %
                    (instance.databaseinfra.user, new_password))
        return new_password
