# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import mock
from django.test import TestCase
from drivers import DriverFactory
from physical.tests import factory as factory_physical
from logical.tests import factory as factory_logical
from logical.models import Database
from ..mysqldb import MySQL


class AbstractTestDriverMongo(TestCase):

    def setUp(self):
        self.databaseinfra = factory_physical.DatabaseInfraFactory()
        self.instance = factory_physical.InstanceFactory(databaseinfra=self.databaseinfra, port=3306)
        self.driver = MySQL(databaseinfra=self.databaseinfra)
        self._mysql_client = None

    def tearDown(self):
        if not Database.objects.filter(databaseinfra_id=self.databaseinfra.id):
            self.databaseinfra.delete()
        if self._mysql_client:
            self._mysql_client.disconnect()
        self.driver = self.databaseinfra = self._mysql_client = None

    @property
    def mysql_client(self):
        if self._mysql_client is None:
            self._mysql_client = self.driver.__mysql_client__(self.instance)
        return self._mysql_client


class MySQLEngineTestCase(AbstractTestDriverMongo):
    """
    Tests MySQL Engine
    """

    def test_mysqldb_app_installed(self):
        self.assertTrue(DriverFactory.is_driver_available("mysqldb"))

    #test mysql methods
    def test_instantiate_mysqldb_using_engine_factory(self):
        self.assertEqual(MySQL, type(self.driver))
        self.assertEqual(self.databaseinfra, self.driver.databaseinfra)

    def test_connection_string(self):
        self.assertEqual("mysql://<user>:<password>@127.0.0.1:3306", self.driver.get_connection())

    def test_get_user(self):
        self.assertEqual(self.databaseinfra.user, self.driver.get_user())

    def test_get_password(self):
        self.assertEqual(self.databaseinfra.password, self.driver.get_password())

    def test_get_default_port(self):
        self.assertEqual(3306, self.driver.default_port)

    # @mock.patch.object(MySQL, 'get_replica_name')
    # def test_connection_string_when_in_replica_set(self, get_replica_name):
    #     self.instance = factory_physical.InstanceFactory(databaseinfra=self.databaseinfra, address='127.0.0.2', port=27018)
    #     get_replica_name.return_value = 'my_repl'
    #     self.assertEqual("mysqldb://<user>:<password>@127.0.0.1:27017,127.0.0.2:27018?replicaSet=my_repl", self.driver.get_connection())
    # 
    def test_connection_with_database(self):
        self.database = factory_logical.DatabaseFactory(name="my_db_url_name", databaseinfra=self.databaseinfra)
        self.assertEqual("mysql://<user>:<password>@127.0.0.1:3306/my_db_url_name", self.driver.get_connection(database=self.database))


# class ManageDatabaseMySQLTestCase(AbstractTestDriverMongo):
#     """ Test case to managing database in mysqldb engine """
# 
#     def setUp(self):
#         super(ManageDatabaseMySQLTestCase, self).setUp()
#         self.database = factory_logical.DatabaseFactory(databaseinfra=self.databaseinfra)
#         # ensure database is dropped
#         self.mysql_client.drop_database(self.database.name)
# 
#     def tearDown(self):
#         if not Database.objects.filter(databaseinfra_id=self.databaseinfra.id):
#             self.database.delete()
#         super(ManageDatabaseMySQLTestCase, self).tearDown()
# 
#     def test_mysqldb_create_database(self):
#         self.assertFalse(self.database.name in self.mysql_client.database_names())
#         self.driver.create_database(self.database)
#         self.assertTrue(self.database.name in self.mysql_client.database_names())
# 
#     def test_mysqldb_remove_database(self):
#         self.driver.create_database(self.database)
#         self.assertTrue(self.database.name in self.mysql_client.database_names())
#         self.driver.remove_database(self.database)
#         self.assertFalse(self.database.name in self.mysql_client.database_names())


# class ManageCredentialsMySQLTestCase(AbstractTestDriverMongo):
#     """ Test case to managing credentials in mysqldb engine """
# 
#     def setUp(self):
#         super(ManageCredentialsMySQLTestCase, self).setUp()
#         self.database = factory_logical.DatabaseFactory(databaseinfra=self.databaseinfra)
#         self.credential = factory_logical.CredentialFactory(database=self.database)
#         self.driver.create_database(self.database)
# 
#     def tearDown(self):
#         self.driver.remove_database(self.database)
#         self.credential.delete()
#         self.database.delete()
#         super(ManageCredentialsMySQLTestCase, self).tearDown()
# 
#     def __find_user__(self, credential):
#         return getattr(self.mysql_client, credential.database.name).system.users.find_one({"user": credential.user})
# 
#     def test_mysqldb_create_credential(self):
#         self.assertIsNone(self.__find_user__(self.credential), "User %s already exists. Invalid test" % self.credential)
#         self.driver.create_user(self.credential)
#         user = self.__find_user__(self.credential)
#         self.assertIsNotNone(user)
#         self.assertEquals(self.credential.user, user['user'])
# 
#     def test_mysqldb_remove_credential(self):
#         self.driver.create_user(self.credential)
#         self.assertIsNotNone(self.__find_user__(self.credential), "Error creating user %s. Invalid test" % self.credential)
#         self.driver.remove_user(self.credential)
#         self.assertIsNone(self.__find_user__(self.credential))


