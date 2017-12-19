# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import mock
from django.conf import settings

from drivers import DriverFactory
from logical.tests import factory as factory_logical
from logical.models import Database
from drivers.redis import Redis, RedisSentinel, RedisCluster
from drivers.tests.base import (BaseRedisDriverTestCase, FakeDriverClient,
                                BaseSingleInstanceUpdateSizesTest,
                                BaseHAInstanceUpdateSizesTest)
from physical.models import Instance
from physical.tests.factory import (DatabaseInfraParameterFactory, CloudStackOfferingFactory,
                                    DatabaseInfraOfferingFactory)


LOG = logging.getLogger(__name__)


class RedisDriverPropertiesTestCase(BaseRedisDriverTestCase):

    def setUp(self):
        super(RedisDriverPropertiesTestCase, self).setUp()
        cs_offering = CloudStackOfferingFactory(memory_size_mb=9)
        DatabaseInfraOfferingFactory(
            databaseinfra=self.databaseinfra,
            offering=cs_offering
        )

    def test_maxmemory_from_parameter(self):
        '''
            Test property: maxmemory from parameter
            case: Validates when maxmemory from parameter table
        '''

        DatabaseInfraParameterFactory(
            value='110000', parameter__name='maxmemory',
            databaseinfra=self.databaseinfra
        )

        self.assertEqual(self.driver.maxmemory, 110000)

    def test_maxmemory_from_configuration(self):
        '''
            Test property: maxmemory from configuration
            case: Validates maxmemory come from configuration
                  when not found on parameter table
        '''

        self.assertEqual(self.driver.maxmemory, 4718592)


@mock.patch('drivers.redis.Redis.redis', new=FakeDriverClient)
class RedisSingleUpdateSizesTestCase(BaseSingleInstanceUpdateSizesTest, BaseRedisDriverTestCase):
    pass


@mock.patch('drivers.redis.Redis.redis', new=FakeDriverClient)
class RedisSentinelUpdateSizesTestCase(BaseRedisDriverTestCase, BaseHAInstanceUpdateSizesTest):

    driver_class = RedisSentinel
    secondary_instance_quantity = 2
    secondary_instance_type = Instance.REDIS_SENTINEL


@mock.patch('drivers.redis.Redis.redis', new=FakeDriverClient)
class RedisClusterUpdateSizesTestCase(BaseRedisDriverTestCase, BaseHAInstanceUpdateSizesTest):

    driver_class = RedisCluster
    instances_quantity = 6


class RedisUsedAndTotalTestCase(BaseRedisDriverTestCase):

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
        self.assertEqual(self.driver.get_master_instance_total_size_in_gb(), 105 * self.GB_FACTOR)
        self.assertEqual(self.driver.masters_used_size_in_bytes, 55)

    def test_masters_single_instance_none(self):
        """
            Test validates return total and used size when has single instance
        """

        self.instance.total_size_in_bytes = None
        self.instance.used_size_in_bytes = None
        self.instance.save()
        self.assertEqual(self.driver.masters_total_size_in_bytes, 0)
        self.assertEqual(self.driver.get_master_instance_total_size_in_gb(), 0)
        self.assertEqual(self.driver.masters_used_size_in_bytes, 0)

    def test_masters_sentinel_instance(self):
        """
            Test validates return total and used size when has sentinel instance
        """
        self.driver = RedisSentinel(databaseinfra=self.databaseinfra)
        self.driver.check_instance_is_master = mock.MagicMock(
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
        self.assertEqual(self.driver.get_master_instance_total_size_in_gb(), 35 * self.GB_FACTOR)
        self.assertEqual(self.driver.masters_used_size_in_bytes, 10)

    def test_masters_cluster_instance(self):
        """
            Test validates return total and used size when has cluster instances
        """
        self.driver = RedisCluster(databaseinfra=self.databaseinfra)
        self.driver.check_instance_is_master = mock.MagicMock(
            side_effect=self.instance_helper.check_instance_is_master
        )
        self.instance_helper.create_instances_by_quant(
            infra=self.databaseinfra, qt=5, base_address='131',
            total_size_in_bytes=50, used_size_in_bytes=25,
            instance_type=self.instance_type
        )
        self.instance.total_size_in_bytes = 50
        self.instance.used_size_in_bytes = 25
        self.instance.save()
        self.assertEqual(self.driver.masters_total_size_in_bytes, 150)
        self.assertEqual(self.driver.get_master_instance_total_size_in_gb(), 50 * self.GB_FACTOR)
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
            'redis://:<password>@{}/0'.format(self.instance_endpoint), self.driver.get_connection())

    def test_get_password(self):
        self.assertEqual(
            self.databaseinfra.password, self.driver.get_password())

    def test_get_default_port(self):
        self.assertEqual(6379, self.driver.default_port)

    def test_connection_with_database(self):
        self.database = factory_logical.DatabaseFactory(
            name="my_db_url_name", databaseinfra=self.databaseinfra)
        self.assertEqual('redis://:<password>@{}/0'.format(self.instance_endpoint),
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
        # instance = self.instances[0]
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
        # self.instance = self.instances[0]
        host = ",".join([
            "{}:{}".format(instance.address, instance.port)
            for instance in self.databaseinfra.instances.filter(
                instance_type=self.instance.REDIS_SENTINEL, is_active=True)
        ])

        url = self.driver.get_connection(None)
        expected = self.get_connection_base.format(
            'sentinel', host, 'service_name:{}'.format(self.databaseinfra.name)
        )

        self.assertEqual(url, expected)
