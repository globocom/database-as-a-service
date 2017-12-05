# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import mock
from django.conf import settings
from drivers import DriverFactory
from logical.tests import factory as factory_logical
from logical.models import Database
from ..redis import Redis, RedisSentinel, RedisCluster
from drivers.tests.base import BaseRedisDriverTestCase, BaseUsedAndTotalTestCase, FakeDriverClient
from physical.models import Instance


LOG = logging.getLogger(__name__)


@mock.patch('drivers.redis.Redis.redis', new=FakeDriverClient)
class RedisSingleUpdateUsedSizeTestCase(BaseRedisDriverTestCase, BaseUsedAndTotalTestCase):

    def test_instance_alive(self):
        self.instance.used_size_in_bytes = 0
        self.instance.save()
        result = self.driver.update_infra_instances_used_size()
        self._validate_instances()
        self.assertListEqual(result['updated'], [self.instance])
        self.assertEqual(result['error'], [])

    def test_instance_dead(self):
        self.instance.used_size_in_bytes = 0
        self.instance.status = Instance.DEAD
        self.instance.save()
        result = self.driver.update_infra_instances_used_size()
        self._validate_instances(expected_used_size=0)
        self.assertListEqual(result['error'], [self.instance])
        self.assertEqual(result['updated'], [])


@mock.patch('drivers.redis.redis', new=FakeDriverClient)
class RedisSentinelUpdateUsedSizeTestCase(BaseRedisDriverTestCase, BaseUsedAndTotalTestCase):

    driver_class = RedisSentinel

    def setUp(self):
        super(RedisSentinelUpdateUsedSizeTestCase, self).setUp()
        instances = self._create_more_instances(3)
        self._change_instance_type(instances[-2:], Instance.REDIS_SENTINEL)

    def test_instance_alive(self):
        self.instance.used_size_in_bytes = 0
        self.instance.save()
        result = self.driver.update_infra_instances_used_size()
        self._validate_instances()
        self.assertListEqual(result['updated'], list(self.databaseinfra.instances.filter(instance_type=Instance.REDIS)))
        self.assertEqual(result['error'], [])

    def test_instance_dead(self):
        self.instance.used_size_in_bytes = 0
        self.instance.status = Instance.DEAD
        self.instance.save()
        result = self.driver.update_infra_instances_used_size()

        self.assertEqual(self.instance.used_size_in_bytes, 0)

        alive_instances = list(self.databaseinfra.instances.filter(
            status=Instance.ALIVE, instance_type=Instance.REDIS
        ))

        self.assertEqual(alive_instances[0].used_size_in_bytes, 40)
        self.assertListEqual(result['error'], [self.instance])
        self.assertEqual(result['updated'], alive_instances)


@mock.patch('drivers.redis.Redis.redis', new=FakeDriverClient)
class RedisClusterUpdateUsedSizeTestCase(BaseRedisDriverTestCase, BaseUsedAndTotalTestCase):

    driver_class = RedisSentinel

    def setUp(self):
        super(RedisClusterUpdateUsedSizeTestCase, self).setUp()
        self._create_more_instances(5, used_size_in_bytes=0)

    def test_instance_alive(self):
        self.instance.used_size_in_bytes = 0
        self.instance.save()
        result = self.driver.update_infra_instances_used_size()
        self._validate_instances()
        self.assertEqual(len(result['updated']), 6)
        self.assertListEqual(result['updated'], list(self.databaseinfra.instances.filter(instance_type=Instance.REDIS)))
        self.assertEqual(result['error'], [])

    def test_instance_dead(self):
        self.instance.used_size_in_bytes = 0
        self.instance.status = Instance.DEAD
        self.instance.save()
        alive_instances = list(self.databaseinfra.instances.filter(
            status=Instance.ALIVE, instance_type=Instance.REDIS
        ))
        another_dead_instance = alive_instances.pop()
        another_dead_instance.status = Instance.DEAD
        another_dead_instance.save()
        result = self.driver.update_infra_instances_used_size()

        self.assertEqual(self.instance.used_size_in_bytes, 0)

        self.assertListEqual(result['error'], [self.instance, another_dead_instance])
        self._validate_instances(instances=result['error'], expected_used_size=0)
        self.assertEqual(len(result['updated']), 4)
        self.assertEqual(result['updated'], alive_instances)
        self._validate_instances(instances=result['updated'], expected_used_size=40)


class RedisUsedAndTotalTestCase(BaseRedisDriverTestCase, BaseUsedAndTotalTestCase):

    """
    Tests Redis total and used
    """

    def test_masters_single_instance(self):
        """
            Test validates return total and used size when has single instance
        """

        self.instance.total_size_in_bytes = 105
        self.instance.used_size_in_bytes = 55
        self.instance.save()
        self.assertEqual(self.driver.masters_total_size_in_bytes, 105)
        self.assertEqual(self.driver.masters_used_size_in_bytes, 55)

    def test_masters_sentinel_instance(self):
        """
            Test validates return total and used size when has sentinel instance
        """
        self.driver = RedisSentinel(databaseinfra=self.databaseinfra)
        self.driver.check_instance_is_master = mock.MagicMock(
            side_effect=self._check_instance_is_master
        )
        self._create_more_instances()
        self.instance.total_size_in_bytes = 35
        self.instance.used_size_in_bytes = 10
        self.instance.save()
        self.assertEqual(self.driver.masters_total_size_in_bytes, 35)
        self.assertEqual(self.driver.masters_used_size_in_bytes, 10)

    def test_masters_cluster_instance(self):
        """
            Test validates return total and used size when has cluster instances
        """
        self.driver = RedisCluster(databaseinfra=self.databaseinfra)
        self.driver.check_instance_is_master = mock.MagicMock(
            side_effect=self._check_instance_is_master
        )
        self._create_more_instances(5)
        self.instance.total_size_in_bytes = 50
        self.instance.used_size_in_bytes = 25
        self.instance.save()
        self.assertEqual(self.driver.masters_total_size_in_bytes, 150)
        self.assertEqual(self.driver.masters_used_size_in_bytes, 75)


class RedisEngineTestCase(BaseRedisDriverTestCase):

    """
    Tests Redis Engine
    """

    def test_redis_app_installed(self):
        self.assertTrue(DriverFactory.is_driver_available("redis_single"))
        self.assertTrue(DriverFactory.is_driver_available("redis_sentinel"))

    # test redis methods
    def test_instantiate_redis_using_engine_factory(self):
        self.assertEqual(Redis, type(self.driver))
        self.assertEqual(self.databaseinfra, self.driver.databaseinfra)

    def test_connection_string(self):
        self.assertEqual(
            "redis://:<password>@{}/0".format(self.endpoint), self.driver.get_connection())

    def test_get_password(self):
        self.assertEqual(
            self.databaseinfra.password, self.driver.get_password())

    def test_get_default_port(self):
        self.assertEqual(6379, self.driver.default_port)

    def test_connection_with_database(self):
        self.database = factory_logical.DatabaseFactory(
            name="my_db_url_name", databaseinfra=self.databaseinfra)
        self.assertEqual("redis://:<password>@{}/0".format(self.endpoint),
                         self.driver.get_connection(database=self.database))


class ManageDatabaseRedisTestCase(BaseRedisDriverTestCase):

    """ Test case to managing database in redis engine """

    def setUp(self):
        super(ManageDatabaseRedisTestCase, self).setUp()
        self.database = factory_logical.DatabaseFactory(
            databaseinfra=self.databaseinfra, address=settings.REDIS_HOST)
        # ensure database is dropped
        # get fake driver
        driver = self.databaseinfra.get_driver()
        driver.remove_database(self.database)

    def tearDown(self):
        if not Database.objects.filter(databaseinfra_id=self.databaseinfra.id):
            self.database.delete()
        super(ManageDatabaseRedisTestCase, self).tearDown()


class ExclusiveMethodsBase(BaseRedisDriverTestCase):

    @property
    def get_connection_base(self):
        return '{}://:<password>@{}/{}'


class ExclusiveMethodsSingle(ExclusiveMethodsBase):

    def setUp(self):
        super(ExclusiveMethodsSingle, self).setUp()

        klass = DriverFactory.get_driver_class("redis_single")
        self.driver = klass(databaseinfra=self.databaseinfra)

        self.instance = self.driver.databaseinfra.instances.first()

    def test_get_connection(self):
        host = '{}:{}'.format(self.instance.address, self.instance.port)

        url = self.driver.get_connection(None)
        expected = self.get_connection_base.format('redis', host, '0')

        self.assertEqual(url, expected)


class ExclusiveMethodsSentinel(ExclusiveMethodsBase):

    def setUp(self):
        super(ExclusiveMethodsSentinel, self).setUp()

        klass = DriverFactory.get_driver_class("redis_sentinel")
        self.driver = klass(databaseinfra=self.databaseinfra)

    def test_get_connection(self):
        host =  ",".join([
            "{}:{}".format(instance.address, instance.port)
            for instance in self.databaseinfra.instances.filter(
                instance_type=self.instance.REDIS_SENTINEL, is_active=True
        )])

        url = self.driver.get_connection(None)
        expected = self.get_connection_base.format(
            'sentinel', host, 'service_name:{}'.format(self.databaseinfra.name)
        )

        self.assertEqual(url, expected)
