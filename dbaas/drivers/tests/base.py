# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import os
from mock import MagicMock

from django.conf import settings
from django.test import TestCase

from physical.tests import factory as factory_physical
from physical.models import Instance
from logical.models import Database, GB_FACTOR
from drivers.mysqldb import MySQL
from drivers.mongodb import MongoDB
from drivers.redis import Redis
from dbaas.tests.helpers import InstanceHelper, UsedAndTotalValidator


class FakeDriverClient(object):

    def __init__(self, instance):
        self.instance = instance

    def __exit__(self, *args, **kw):
        pass

    def __enter__(self):
        return self

    def info(self):
        """
        Mock for redis driver
        """
        return {
            'used_memory': 40
        }

    @property
    def admin(self):
        """
        Mock for pymongo driver
        """

        return type(str('FakeCommand'),
                    (object,),
                    {'command': lambda self, string: {'totalSize': 40}})()


class BaseDriverTest(object):

    GB_FACTOR = GB_FACTOR
    host = None
    port = None
    db_user = 'admin'
    db_password = '123456'
    engine_name = ''
    instance_type = None
    driver_class = None
    driver_client_lookup = ''
    instances_quantity = 1
    instance_helper = InstanceHelper

    def setUp(self):
        host = self.host or '127.0.0.1'
        port = self.port or 3306
        self.infra_endpoint = '{}:{}'.format(host, port)
        self.databaseinfra = factory_physical.DatabaseInfraFactory(
            password=self.db_password, endpoint="{}:{}".format(host, port),
            engine__engine_type__name=self.engine_name, user=self.db_user
        )
        hostname = factory_physical.HostFactory()
        self.nfsaas_host_attr = factory_physical.NFSaaSHostAttr(
            host=hostname,
            nfsaas_used_size_kb=float(40.0/1024.0)
        )
        self.instances = self.instance_helper.create_instances_by_quant(
            infra=self.databaseinfra, port=self.port, qt=self.instances_quantity,
            total_size_in_bytes=0, used_size_in_bytes=0,
            instance_type=self.instance_type, hostname=hostname
        )
        self.instance = self.instances[0]
        self.instance_endpoint = "{}:{}".format(self.instance.address, self.instance.port)
        self.driver = self.driver_class(databaseinfra=self.databaseinfra)
        self._driver_client = None

    def tearDown(self):
        factory_physical.HostFactory.FACTORY_FOR.objects.all().delete()
        Instance.objects.all().delete()
        if not Database.objects.filter(databaseinfra_id=self.databaseinfra.id):
            self.databaseinfra.delete()
        if self._driver_client:
            self.driver_client.close()

    @property
    def driver_client(self):
        if self._driver_client is None:
            get_driver_func = getattr(
                self.driver, self.driver_client_lookup
            )
            self._driver_client = get_driver_func(self.instance)
        return self._driver_client


class BaseMysqlDriverTestCase(BaseDriverTest, TestCase):

    host = settings.DB_HOST
    port = 3306
    db_user = 'root'
    db_password = settings.DB_PASSWORD
    engine_name = 'mysql'
    instance_type = 1
    driver_class = MySQL
    driver_client_lookup = '__mysql_client__'


class BaseMongoDriverTestCase(BaseDriverTest, TestCase):

    host = os.getenv('TESTS_MONGODB_HOST', '127.0.0.1')
    port = os.getenv('TESTS_MONGODB_PORT', '27017')
    engine_name = 'mongodb'
    instance_type = 2
    driver_class = MongoDB
    driver_client_lookup = '__mongo_client__'


class BaseRedisDriverTestCase(BaseDriverTest, TestCase):

    host = '127.0.0.1'
    port = settings.REDIS_PORT
    db_password = 'OPlpplpooi'
    engine_name = 'redis'
    instance_type = 4
    driver_class = Redis
    driver_client_lookup = '__redis_client__'


def make_expected_instances(instances, prefix):
    return map(lambda i: '{}{}'.format(i.dns, prefix), instances)


class BaseSingleInstanceUpdateSizesTest(BaseDriverTest):

    instances_quantity = 1
    validator_helper = UsedAndTotalValidator

    def setUp(self):
        super(BaseSingleInstanceUpdateSizesTest, self).setUp()
        self.driver.check_instance_is_master = MagicMock(
            side_effect=self.instance_helper.check_instance_is_master
        )

    def test_instance_alive(self):
        self.driver.databaseinfra.get_parameter_value_by_parameter_name = MagicMock(return_value=90)
        result = self.driver.update_infra_instances_sizes()
        self.validator_helper.instances_sizes(self.driver.get_database_instances())
        self.assertListEqual(result, make_expected_instances(
            self.instances[:1], ' - OK\n')
        )

    def test_instance_dead(self):
        self.instance_helper.kill_instances(self.instances)
        result = self.driver.update_infra_instances_sizes()
        self.validator_helper.instances_sizes(
            self.driver.get_database_instances(),
            expected_used_size=0,
            expected_total_size=0
        )
        self.assertListEqual(result, make_expected_instances(
            self.instances[:1], ' - ERROR\n')
        )


class BaseHAInstanceUpdateSizesTest(BaseDriverTest):

    validator_helper = UsedAndTotalValidator
    instances_quantity = 4
    secondary_instance_quantity = None
    secondary_instance_type = None
    dead_instance_quantity = 1

    def setUp(self):
        super(BaseHAInstanceUpdateSizesTest, self).setUp()
        if self.secondary_instance_quantity is not None:
            self.instance_helper.change_instances_type(
                self.instances[-self.secondary_instance_quantity:],
                self.secondary_instance_type
            )
        self.driver.databaseinfra.get_parameter_value_by_parameter_name = MagicMock(return_value=90)

    def test_instance_alive(self):
        updated_instances = self.driver.update_infra_instances_sizes()
        database_instances = self.driver.get_database_instances()
        self.validator_helper.instances_sizes(
            database_instances
        )

        expected_result = make_expected_instances(database_instances, ' - OK\n')
        self.assertListEqual(updated_instances, expected_result)

    def test_instance_dead(self):
        self.instance_helper.kill_instances(self.instances[self.dead_instance_quantity:])
        instances = self.driver.update_infra_instances_sizes()

        all_instances = self.databaseinfra.instances.filter(
            instance_type=self.instance_type
        )
        alive_instances = all_instances.filter(status=Instance.ALIVE)
        dead_instances = all_instances.exclude(status=Instance.ALIVE)

        self.validator_helper.instances_sizes(alive_instances)
        self.validator_helper.instances_sizes(
            dead_instances,
            expected_used_size=0,
            expected_total_size=0
        )

        expected_error_instances = make_expected_instances(
            dead_instances, ' - ERROR\n'
        )
        expected_updated_instances = make_expected_instances(
            alive_instances, ' - OK\n'
        )

        self.assertListEqual(
            instances, expected_updated_instances + expected_error_instances
        )
