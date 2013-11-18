# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import re
import _mysql as mysqldb
import _mysql_exceptions
from contextlib import contextmanager
from . import BaseDriver, AuthenticationError, ConnectionError, GenericDriverError
from util import make_db_random_password

LOG = logging.getLogger(__name__)


class MySQL(BaseDriver):

    default_port = 3306

    def get_connection(self):
        my_instance = self.databaseinfra.instances.get(databaseinfra__name=self.databaseinfra.name)
        return "mysql://<user>:<password>@%s" % (my_instance.address)

    def __get_admin_connection(self, instance=None):
        if instance:
            return instance.address, instance.port
        my_instance = self.databaseinfra.instances.get(databaseinfra__name=self.databaseinfra.name)
        return my_instance.address, my_instance.port

    def __mysql_client__(self, instance, database='mysql'):
        connection_address, connection_port = self.__get_admin_connection(instance)
        try:
            LOG.debug('Connecting to mysql databaseinfra %s', self.databaseinfra)
            client = mysqldb.connect(host=connection_address, port=int(connection_port),
                                     user=self.databaseinfra.user, passwd=self.databaseinfra.password,
                                     db=database, connect_timeout=5)
            LOG.debug('Successfully connected to mysql databaseinfra %s', self.databaseinfra)
            return client
        except Exception, e:
            raise e

    @contextmanager
    def mysqldb(self, instance=None, database=None):
        client = None
        try:
            # instance = instance or self.databaseinfra.instances
            yield self.__mysql_client__(instance)
            # return_value = client
            # yield return_value
        except _mysql_exceptions.OperationalError, e:
            if re.search("Access denied", e.args[1]):
                LOG.debug('Successfully connected to mysql databaseinfra %s', self.databaseinfra)
                raise AuthenticationError(e.args[1])
            elif re.search("Can't connect to MySQL", e.args[1]):
                raise ConnectionError(e.args[1])
            else:
                print "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ Erro generico: %s" % type(e)
                raise GenericDriverError
        finally:
            try:
                if client:
                    LOG.debug('Disconnecting mysql databaseinfra %s', self.databaseinfra)
                    client.close()
            except:
                LOG.warn('Error disconnecting from databaseinfra %s. Ignoring...', self.databaseinfra, exc_info=True)

    def check_status(self, instance=None):
        with self.mysqldb(instance=instance) as client:
            try:
                client.query("""SELECT 1""")
            except _mysql_exceptions.OperationalError, e:
                raise ConnectionError(e.args[1])

    def info(self):
        pass

    def create_database(self, database):
        LOG.info("creating database %s" % database.name)
        with self.mysqldb(database=database) as mysql_database:
            mysql_database.query("CREATE DATABASE %s" % database.name)

    def create_user(self, credential, roles=["readWrite", "dbAdmin"]):
        LOG.info("creating user %s to %s" % (credential.user, credential.database))
        with self.mysqldb(database=credential.database) as mysql_database:
            # the first release will allow every host to connect to new database
            mysql_database.query("GRANT ALL PRIVILEGES ON %s.* TO '%s'@'localhost' IDENTIFIED BY '%s'" %
                                (credential.database, credential.user, credential.password, ))

    def remove_database(self, database):
        LOG.info("removing database %s" % database.name)
        with self.mysqldb() as mysql_database:
            mysql_database.query("DROP DATABASE %s" % database.name)

    def update_user(self, credential):
        self.create_user(credential)

    def remove_user(self, credential):
        LOG.info("removing user %s from %s" % (credential.user, credential.database))
        with self.mysqldb(database=credential.database) as mysql_database:
            mysql_database.query("DROP USER '%s'@'localhost'" % credential.user)

    def change_default_pwd(self, instance):
        with self.mysqldb(instance=instance) as client:
            new_password = make_db_random_password()
            client.query("SET PASSWORD FOR '%s'@'localhost' = PASSWORD('%s')" %
                        (instance.databaseinfra.user, new_password))
            return new_password
