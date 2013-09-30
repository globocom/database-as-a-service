# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.test import TestCase
from base.driver import DriverFactory
from base.tests import factory
from ..driver_pymongo import MongoDB
import pymongo


class AbstractTestDriverMongo(TestCase):

    def setUp(self):
        self.instance = factory.InstanceFactory()
        self.driver = MongoDB(instance=self.instance)
        self._mongo_client = None

    def tearDown(self):
        self.instance.delete()
        if self._mongo_client:
            self._mongo_client.disconnect()
        self.driver = self.instance = self._mongo_client = None

    @property
    def mongo_client(self):
        if self._mongo_client is None:
            self._mongo_client = pymongo.MongoClient(self.instance.node.address, self.instance.node.port)
        return self._mongo_client


class MongoDBEngineTestCase(AbstractTestDriverMongo):
    """
    Tests MongoDB Engine
    """

    def test_mongodb_app_installed(self):
        self.assertTrue(DriverFactory.is_driver_available("mongodb")) 

    #test mongo methods
    def test_instantiate_mongodb_using_engine_factory(self):
        mongodb_engine = DriverFactory.factory(self.instance)
        self.assertEqual(MongoDB, type(mongodb_engine))
        self.assertEqual(self.instance, mongodb_engine.instance)

    def test_connection_string(self):
        self.assertEqual("%s:%s" % (self.instance.node.address, self.instance.node.port), self.driver.get_connection())

    def test_get_user(self):
        self.assertEqual(self.instance.user, self.driver.get_user())

    def test_get_password(self):
        self.assertEqual(self.instance.password, self.driver.get_password())


class ManageDatabaseMongoDBTestCase(AbstractTestDriverMongo):
    """ Test case to managing database in mongodb engine """

    def setUp(self):
        super(ManageDatabaseMongoDBTestCase, self).setUp()
        self.database = factory.DatabaseFactory(instance=self.instance)
        # ensure database is dropped
        self.mongo_client.drop_database(self.database.name)

    def tearDown(self):
        self.database.delete()
        super(ManageDatabaseMongoDBTestCase, self).tearDown()

    def test_mongodb_create_database(self):
        self.assertFalse(self.database.name in self.mongo_client.database_names())
        self.driver.create_database(self.database)
        self.assertTrue(self.database.name in self.mongo_client.database_names())

    def test_mongodb_remove_database(self):
        self.driver.create_database(self.database)
        self.assertTrue(self.database.name in self.mongo_client.database_names())
        self.driver.remove_database(self.database)
        self.assertFalse(self.database.name in self.mongo_client.database_names())


class ManageCredentialsMongoDBTestCase(AbstractTestDriverMongo):
    """ Test case to managing credentials in mongodb engine """

    def setUp(self):
        super(ManageCredentialsMongoDBTestCase, self).setUp()
        self.database = factory.DatabaseFactory(instance=self.instance)
        self.credential = factory.CredentialFactory(database=self.database)
        self.driver.create_database(self.database)

    def tearDown(self):
        self.driver.remove_database(self.database)
        self.credential.delete()
        self.database.delete()
        super(ManageCredentialsMongoDBTestCase, self).tearDown()

    def __find_user__(self, credential):
        return getattr(self.mongo_client, credential.database.name).system.users.find_one({"user": credential.user})

    def test_mongodb_create_credential(self):
        self.assertIsNone(self.__find_user__(self.credential))
        self.driver.create_user(self.credential)
        user = self.__find_user__(self.credential)
        self.assertIsNotNone(user)
        self.assertEquals(self.credential.user, user['user'])

    def test_mongodb_remove_credential(self):
        self.driver.create_user(self.credential)
        self.assertIsNotNone(self.__find_user__(self.credential))
        self.driver.remove_user(self.credential)
        self.assertIsNone(self.__find_user__(self.credential))


