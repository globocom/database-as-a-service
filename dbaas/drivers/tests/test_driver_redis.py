# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import mock
import logging
from django.test import TestCase
from drivers import DriverFactory
from physical.tests import factory as factory_physical
from logical.tests import factory as factory_logical
from logical.models import Database
from ..redis import Redis

LOG = logging.getLogger(__name__)

class AbstractTestDriverRedis(TestCase):

    def setUp(self):
        self.databaseinfra = factory_physical.DatabaseInfraFactory(password="OPlpplpooi", endpoint="127.0.0.1:6379")
        self.instance = factory_physical.InstanceFactory(databaseinfra=self.databaseinfra, port=6379)
        self.driver = Redis(databaseinfra=self.databaseinfra)
        self._redis_client = None

    def tearDown(self):
        if not Database.objects.filter(databaseinfra_id=self.databaseinfra.id):
            self.databaseinfra.delete()
        self.driver = self.databaseinfra = self._redis_client = None

    @property
    def redis_client(self):
        if self._redis_client is None:
            self._redis_client = self.driver.__redis_client__(self.instance)
        return self._redis_client


class RedisEngineTestCase(AbstractTestDriverRedis):
    """
    Tests Redis Engine
    """

    def test_redis_app_installed(self):
        self.assertTrue(DriverFactory.is_driver_available("redis"))

    #test redis methods
    def test_instantiate_redis_using_engine_factory(self):
        self.assertEqual(Redis, type(self.driver))
        self.assertEqual(self.databaseinfra, self.driver.databaseinfra)

    def test_connection_string(self):
        self.assertEqual("redis://:<password>@127.0.0.1:6379/0", self.driver.get_connection())

    def test_get_password(self):
        self.assertEqual(self.databaseinfra.password, self.driver.get_password())

    def test_get_default_port(self):
        self.assertEqual(6379, self.driver.default_port)

    def test_connection_with_database(self):
        self.database = factory_logical.DatabaseFactory(name="my_db_url_name", databaseinfra=self.databaseinfra)
        self.assertEqual("redis://:<password>@127.0.0.1:6379/0", self.driver.get_connection(database=self.database))


class ManageDatabaseRedisTestCase(AbstractTestDriverRedis):
    """ Test case to managing database in redis engine """

    def setUp(self):
        super(ManageDatabaseRedisTestCase, self).setUp()
        self.database = factory_logical.DatabaseFactory(databaseinfra=self.databaseinfra)
        # ensure database is dropped
        #get fake driver
        driver = self.databaseinfra.get_driver()
        driver.remove_database(self.database)

    def tearDown(self):
        if not Database.objects.filter(databaseinfra_id=self.databaseinfra.id):
            self.database.delete()
        super(ManageDatabaseRedisTestCase, self).tearDown()
