# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import mock
from django.test import TestCase
from drivers import DriverFactory
from physical.tests import factory as factory_physical
from logical.tests import factory as factory_logical
from logical.models import Database
from ..mongodb import MongoDB


class AbstractTestDriverMongo(TestCase):

    def setUp(self):
        self.databaseinfra = factory_physical.DatabaseInfraFactory()
        self.instance = factory_physical.InstanceFactory(
            databaseinfra=self.databaseinfra)
        self.driver = MongoDB(databaseinfra=self.databaseinfra)
        self._mongo_client = None

    def tearDown(self):
        if not Database.objects.filter(databaseinfra_id=self.databaseinfra.id):
            self.databaseinfra.delete()
        if self._mongo_client:
            self._mongo_client.close()
        self.driver = self.databaseinfra = self._mongo_client = None

    @property
    def mongo_client(self):
        if self._mongo_client is None:
            self._mongo_client = self.driver.__mongo_client__(self.instance)
        return self._mongo_client


class MongoDBEngineTestCase(AbstractTestDriverMongo):

    """
    Tests MongoDB Engine
    """

    def test_mongodb_app_installed(self):
        self.assertTrue(DriverFactory.is_driver_available("mongodb"))

    # test mongo methods
    def test_instantiate_mongodb_using_engine_factory(self):
        self.assertEqual(MongoDB, type(self.driver))
        self.assertEqual(self.databaseinfra, self.driver.databaseinfra)

    def test_connection_string(self):
        self.assertEqual(
            "mongodb://<user>:<password>@127.0.0.1:27017", self.driver.get_connection())

    def test_get_user(self):
        self.assertEqual(self.databaseinfra.user, self.driver.get_user())

    def test_get_password(self):
        self.assertEqual(
            self.databaseinfra.password, self.driver.get_password())

    def test_get_default_port(self):
        self.assertEqual(27017, self.driver.default_port)

    @mock.patch.object(MongoDB, 'get_replica_name')
    def test_connection_string_when_in_replica_set(self, get_replica_name):
        self.instance = factory_physical.InstanceFactory(
            databaseinfra=self.databaseinfra, address='127.0.0.2', port=27018)
        get_replica_name.return_value = 'my_repl'
        self.assertEqual(
            "mongodb://<user>:<password>@127.0.0.1:27017,127.0.0.2:27018?replicaSet=my_repl", self.driver.get_connection())

    def test_connection_with_database(self):
        self.database = factory_logical.DatabaseFactory(
            name="my_db_url_name", databaseinfra=self.databaseinfra)
        self.assertEqual("mongodb://<user>:<password>@127.0.0.1:27017/my_db_url_name",
                         self.driver.get_connection(database=self.database))

    @mock.patch.object(MongoDB, 'get_replica_name')
    def test_connection_with_database_and_replica(self, get_replica_name):
        self.instance = factory_physical.InstanceFactory(
            databaseinfra=self.databaseinfra, address='127.0.0.2', port=27018)
        get_replica_name.return_value = 'my_repl'
        self.database = factory_logical.DatabaseFactory(
            name="my_db_url_name", databaseinfra=self.databaseinfra)
        self.assertEqual("mongodb://<user>:<password>@127.0.0.1:27017,127.0.0.2:27018/my_db_url_name?replicaSet=my_repl",
                         self.driver.get_connection(database=self.database))


class ManageDatabaseMongoDBTestCase(AbstractTestDriverMongo):

    """ Test case to managing database in mongodb engine """

    def setUp(self):
        super(ManageDatabaseMongoDBTestCase, self).setUp()
        self.database = factory_logical.DatabaseFactory(
            databaseinfra=self.databaseinfra)
        # ensure database is dropped
        self.mongo_client.drop_database(self.database.name)

    def tearDown(self):
        if not Database.objects.filter(databaseinfra_id=self.databaseinfra.id):
            self.database.delete()
        super(ManageDatabaseMongoDBTestCase, self).tearDown()

    def test_mongodb_create_database(self):
        self.assertFalse(
            self.database.name in self.mongo_client.database_names())
        self.driver.create_database(self.database)
        self.assertTrue(
            self.database.name in self.mongo_client.database_names())

    def test_mongodb_remove_database(self):
        self.driver.create_database(self.database)
        self.assertTrue(
            self.database.name in self.mongo_client.database_names())
        self.driver.remove_database(self.database)
        self.assertFalse(
            self.database.name in self.mongo_client.database_names())


class ManageCredentialsMongoDBTestCase(AbstractTestDriverMongo):

    """ Test case to managing credentials in mongodb engine """

    def setUp(self):
        super(ManageCredentialsMongoDBTestCase, self).setUp()
        self.database = factory_logical.DatabaseFactory(
            databaseinfra=self.databaseinfra)
        self.credential = factory_logical.CredentialFactory(
            database=self.database)
        self.driver.create_database(self.database)

    def tearDown(self):
        self.driver.remove_database(self.database)
        self.credential.delete()
        self.database.delete()
        super(ManageCredentialsMongoDBTestCase, self).tearDown()

    def __find_user__(self, credential):
        v = self.mongo_client.server_info()['version']
        if v < '2.6':
            return getattr(self.mongo_client, credential.database.name).system.users.find_one({"user": credential.user})
        else:
            return getattr(self.mongo_client, "admin").system.users.find_one({"user": credential.user, "db": credential.database.name})

    def test_mongodb_create_credential(self):
        self.assertIsNone(self.__find_user__(
            self.credential), "User %s already exists. Invalid test" % self.credential)
        self.driver.create_user(self.credential)
        user = self.__find_user__(self.credential)
        self.assertIsNotNone(user)
        self.assertEquals(self.credential.user, user['user'])
        self.driver.remove_user(self.credential)

    def test_mongodb_remove_credential(self):
        self.driver.create_user(self.credential)
        self.assertIsNotNone(self.__find_user__(
            self.credential), "Error creating user %s. Invalid test" % self.credential)
        self.driver.remove_user(self.credential)
        self.assertIsNone(self.__find_user__(self.credential))
