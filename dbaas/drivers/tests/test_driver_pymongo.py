# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import os
import mock
from drivers import DriverFactory
from physical.tests import factory as factory_physical
from logical.tests import factory as factory_logical
from logical.models import Database
from ..mongodb import MongoDB, MongoDBReplicaSet
from drivers.tests.base import BaseDriverTestCase


class AbstractTestDriverMongo(BaseDriverTestCase):

    host = os.getenv('TESTS_MONGODB_HOST', '127.0.0.1')
    port = os.getenv('TESTS_MONGODB_PORT', '27017')
    engine_type = 'mongodb'
    instance_type = 2
    driver_class = MongoDB
    driver_client_lookup = '__mongo_client__'

#    def setUp(self):
#        mongo_host = os.getenv('TESTS_MONGODB_HOST', '127.0.0.1')
#        mongo_port = os.getenv('TESTS_MONGODB_PORT', '27017')
#        self.mongo_endpoint = '{}:{}'.format(mongo_host, mongo_port)
#        self.databaseinfra = factory_physical.DatabaseInfraFactory(
#            engine__engine_type__name='mongodb'
#        )
#        self.instance = factory_physical.InstanceFactory(
#            databaseinfra=self.databaseinfra, address=mongo_host,
#            instance_type=2)
#        self.driver = MongoDB(databaseinfra=self.databaseinfra)
#        self._mongo_client = None
#
#    def tearDown(self):
#        if not Database.objects.filter(databaseinfra_id=self.databaseinfra.id):
#            self.databaseinfra.delete()
#        if self._mongo_client:
#            self._mongo_client.close()
#        self.driver = self.databaseinfra = self._mongo_client = None

    @property
    def mongo_client(self):
        return self.driver_client


class MongoUsedAndTotalTestCase(AbstractTestDriverMongo):

    """
    Tests Mongo total and used
    """

    def setUp(self):
        super(MongoUsedAndTotalTestCase, self).setUp()
        self.masters_quantity = 1
        self.driver.check_instance_is_master = mock.MagicMock(
            side_effect=self._check_instance_is_master
        )

    def _check_instance_is_master(self, instance):

        n = int(instance.address.split('.')[-1]) - 1

        return n % 2 == 0

    def _create_more_instances(self, qt=1, total_size_in_bytes=50):

        def _create(n):
            n += 2
            return factory_physical.InstanceFactory(
                databaseinfra=self.databaseinfra,
                address='127.{0}.{0}.{0}'.format(n), instance_type=2,
                total_size_in_bytes=total_size_in_bytes
            )

        return map(_create, range(qt))

    def test_masters_single_instance(self):
        """
            Test validates return total and used size when has single instance
        """

        self.instance.total_size_in_bytes = 105
        self.instance.used_size_in_bytes = 55
        self.instance.save()
        self.assertEqual(self.driver.masters_total_size_in_bytes, 105)
        self.assertEqual(self.driver.masters_used_size_in_bytes, 55)

    def test_masters_replicaset_instance(self):
        """
            Test validates return total and used size when has single instance
        """
        self.driver = MongoDBReplicaSet(databaseinfra=self.databaseinfra)
        self.driver.check_instance_is_master = mock.MagicMock(
            side_effect=self._check_instance_is_master
        )
        self._create_more_instances()
        self.instance.total_size_in_bytes = 35
        self.instance.used_size_in_bytes = 10
        self.instance.save()
        self.assertEqual(self.driver.masters_total_size_in_bytes, 35)
        self.assertEqual(self.driver.masters_used_size_in_bytes, 10)


class MongoDBEngineTestCase(AbstractTestDriverMongo):

    """
    Tests MongoDB Engine
    """

    def test_mongodb_app_installed(self):
        self.assertTrue(DriverFactory.is_driver_available("mongodb_single"))
        self.assertTrue(DriverFactory.is_driver_available("mongodb_replica_set"))

    # test mongo methods
    def test_instantiate_mongodb_using_engine_factory(self):
        self.assertEqual(MongoDB, type(self.driver))
        self.assertEqual(self.databaseinfra, self.driver.databaseinfra)

    def test_connection_string(self):
        self.assertEqual(
            "mongodb://<user>:<password>@{}".format(self.endpoint), self.driver.get_connection())

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

        expected_conn = ("mongodb://<user>:<password>"
                          "@{},127.0.0.2:27018"
                          "?replicaSet=my_repl").format(self.endpoint)

        self.assertEqual(expected_conn, self.driver.get_connection())

    def test_connection_with_database(self):
        self.database = factory_logical.DatabaseFactory(
            name="my_db_url_name", databaseinfra=self.databaseinfra)

        expected_conn = ("mongodb://<user>:<password>"
                         "@{}/my_db_url_name").format(self.endpoint)

        self.assertEqual(expected_conn, self.driver.get_connection(database=self.database))

    @mock.patch.object(MongoDB, 'get_replica_name')
    def test_connection_with_database_and_replica(self, get_replica_name):
        self.instance = factory_physical.InstanceFactory(
            databaseinfra=self.databaseinfra, address='127.0.0.2', port=27018)
        get_replica_name.return_value = 'my_repl'
        self.database = factory_logical.DatabaseFactory(
            name="my_db_url_name", databaseinfra=self.databaseinfra)

        expected_conn = ("mongodb://<user>:<password>"
                         "@{},127.0.0.2:27018/my_db_url_name"
                         "?replicaSet=my_repl").format(self.endpoint)

        self.assertEqual(expected_conn, self.driver.get_connection(database=self.database))


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
