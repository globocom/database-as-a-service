# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import os
from mock import patch, MagicMock

from drivers import DriverFactory
from physical.tests import factory as factory_physical
from logical.tests import factory as factory_logical
from logical.models import Database
from drivers.mongodb import MongoDB, MongoDBReplicaSet
from drivers.tests.base import (BaseMongoDriverTestCase, FakeDriverClient,
                                BaseSingleInstanceUpdateSizesTest,
                                BaseHAInstanceUpdateSizesTest)
from physical.models import Instance


@patch('drivers.mongodb.MongoDB.pymongo', new=FakeDriverClient)
@patch('physical.models.DiskOffering.size_bytes', new=MagicMock(return_value=90))
class MongoSingleUpdateSizesTestCase(BaseSingleInstanceUpdateSizesTest, BaseMongoDriverTestCase):
    pass


@patch('drivers.mongodb.MongoDB.pymongo', new=FakeDriverClient)
@patch('physical.models.DiskOffering.size_bytes', new=MagicMock(return_value=90))
class MongoReplicaSetUpdateSizesTestCase(BaseMongoDriverTestCase, BaseHAInstanceUpdateSizesTest):

    driver_class = MongoDBReplicaSet
    secondary_instance_quantity = 2
    secondary_instance_type = Instance.MONGODB_ARBITER


class MongoUsedAndTotalTestCase(BaseMongoDriverTestCase):

    """
    Tests Mongo total and used
    """

    def test_masters_single_instance(self):
        """
            Test validates return total and used size when has single instance
        """

        self.instance.total_size_in_bytes = 105
        self.instance.used_size_in_bytes = 55
        self.instance.save()
        self.assertEqual(self.driver.masters_total_size_in_bytes, 105)
        expected_total_size_in_gb = 105 * self.GB_FACTOR
        self.assertEqual(self.driver.get_master_instance_total_size_in_gb(), expected_total_size_in_gb)
        self.assertEqual(self.driver.masters_used_size_in_bytes, 55)

    def test_masters_replicaset_instance(self):
        """
            Test validates return total and used size when has single instance
        """
        self.driver = MongoDBReplicaSet(databaseinfra=self.databaseinfra)
        self.driver.check_instance_is_master = MagicMock(
            side_effect=self.instance_helper.check_instance_is_master
        )
        self.instance_helper.create_instances_by_quant(
            infra=self.databaseinfra, base_address='131',
            instance_type=self.instance_type,
            total_size_in_bytes=35, used_size_in_bytes=10
        )

        self.instance.total_size_in_bytes = 35
        self.instance.used_size_in_bytes = 10
        self.instance.save()
        self.assertEqual(self.driver.masters_total_size_in_bytes, 35)
        expected_total_size_in_gb = 35 * self.GB_FACTOR
        self.assertEqual(self.driver.get_master_instance_total_size_in_gb(), expected_total_size_in_gb)
        self.assertEqual(self.driver.masters_used_size_in_bytes, 10)


class MongoDBEngineTestCase(BaseMongoDriverTestCase):

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
            "mongodb://<user>:<password>@{}".format(self.instance_endpoint), self.driver.get_connection())

    def test_get_user(self):
        self.assertEqual(self.databaseinfra.user, self.driver.get_user())

    def test_get_password(self):
        self.assertEqual(
            self.databaseinfra.password, self.driver.get_password())

    def test_get_default_port(self):
        self.assertEqual(27017, self.driver.default_port)

    @patch.object(MongoDB, 'get_replica_name')
    def test_connection_string_when_in_replica_set(self, get_replica_name):
        self.instance = factory_physical.InstanceFactory(
            databaseinfra=self.databaseinfra, address='127.0.0.2', port=27018)
        get_replica_name.return_value = 'my_repl'

        expected_conn = ("mongodb://<user>:<password>"
                          "@{},127.0.0.2:27018"
                          "?replicaSet=my_repl").format(self.instance_endpoint)

        self.assertEqual(expected_conn, self.driver.get_connection())

    def test_connection_with_database(self):
        self.database = factory_logical.DatabaseFactory(
            name="my_db_url_name", databaseinfra=self.databaseinfra)

        expected_conn = ("mongodb://<user>:<password>"
                         "@{}/my_db_url_name").format(self.instance_endpoint)

        self.assertEqual(expected_conn, self.driver.get_connection(database=self.database))

    @patch.object(MongoDB, 'get_replica_name')
    def test_connection_with_database_and_replica(self, get_replica_name):
        self.instance = factory_physical.InstanceFactory(
            databaseinfra=self.databaseinfra, address='127.0.0.2', port=27018)
        get_replica_name.return_value = 'my_repl'
        self.database = factory_logical.DatabaseFactory(
            name="my_db_url_name", databaseinfra=self.databaseinfra)

        expected_conn = ("mongodb://<user>:<password>"
                         "@{},127.0.0.2:27018/my_db_url_name"
                         "?replicaSet=my_repl").format(self.instance_endpoint)

        self.assertEqual(expected_conn, self.driver.get_connection(database=self.database))


class ManageDatabaseMongoDBTestCase(BaseMongoDriverTestCase):

    """ Test case to managing database in mongodb engine """

    def setUp(self):
        super(ManageDatabaseMongoDBTestCase, self).setUp()
        self.database = factory_logical.DatabaseFactory(
            databaseinfra=self.databaseinfra)
        self.instance.address = os.getenv('TESTS_MONGODB_HOST', '127.0.0.1')
        self.instance.save()
        # ensure database is dropped
        self.driver_client.drop_database(self.database.name)

    def tearDown(self):
        if not Database.objects.filter(databaseinfra_id=self.databaseinfra.id):
            self.database.delete()
        super(ManageDatabaseMongoDBTestCase, self).tearDown()

    def test_mongodb_create_database(self):
        self.assertFalse(
            self.database.name in self.driver_client.database_names())
        self.driver.create_database(self.database)
        self.assertTrue(
            self.database.name in self.driver_client.database_names())

    def test_mongodb_remove_database(self):
        self.driver.create_database(self.database)
        self.assertTrue(
            self.database.name in self.driver_client.database_names())
        self.driver.remove_database(self.database)
        self.assertFalse(
            self.database.name in self.driver_client.database_names())


class ManageCredentialsMongoDBTestCase(BaseMongoDriverTestCase):

    """ Test case to managing credentials in mongodb engine """

    def setUp(self):
        super(ManageCredentialsMongoDBTestCase, self).setUp()
        self.database = factory_logical.DatabaseFactory(
            databaseinfra=self.databaseinfra)
        self.credential = factory_logical.CredentialFactory(
            database=self.database)
        self.instance.address = os.getenv('TESTS_MONGODB_HOST', '127.0.0.1')
        # self.instance.address = '127.0.0.1'
        self.instance.save()
        self.driver.create_database(self.database)

    def tearDown(self):
        self.driver.remove_database(self.database)
        self.credential.delete()
        self.database.delete()
        super(ManageCredentialsMongoDBTestCase, self).tearDown()

    def __find_user__(self, credential):
        v = self.driver_client.server_info()['version']
        if v < '2.6':
            return getattr(self.driver_client, credential.database.name).system.users.find_one({"user": credential.user})
        else:
            return getattr(self.driver_client, "admin").system.users.find_one({"user": credential.user, "db": credential.database.name})

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
