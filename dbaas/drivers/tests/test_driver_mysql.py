# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from mock import MagicMock, patch
import logging
from drivers import DriverFactory
from drivers.tests.base import (BaseMysqlDriverTestCase,
                                BaseSingleInstanceUpdateSizesTest,
                                BaseHAInstanceUpdateSizesTest)
from logical.tests import factory as factory_logical
from logical.models import Database
from ..mysqldb import MySQL, MySQLFOXHA
from physical.models import Instance

LOG = logging.getLogger(__name__)


FAKE_QUERY_RESULT = (
    {'Size': '15', 'Database': 'fake_name'},
    {'Size': '13', 'Database': 'information_schema'},
    {'Size': '7', 'Database': 'mysql'},
    {'Size': '5', 'Database': 'performance_schema'}
)


@patch('drivers.mysqldb.MySQL.query', new=MagicMock(return_value=FAKE_QUERY_RESULT))
@patch('physical.models.DiskOffering.size_bytes', new=MagicMock(return_value=90))
class MySQLSingleUpdateUsedSizeTestCase(BaseMysqlDriverTestCase, BaseSingleInstanceUpdateSizesTest):

    pass
#    def test_instance_alive(self, mock_query):
#        self.instance.used_size_in_bytes = 0
#        self.instance.save()
#        result = self.driver.update_infra_instances_used_size()
#        self._validate_instances()
#        self.assertListEqual(result['updated'], [self.instance])
#        self.assertEqual(result['error'], [])
#
#    def test_instance_dead(self, mock_query):
#        self.instance.used_size_in_bytes = 0
#        self.instance.status = Instance.DEAD
#        self.instance.save()
#        result = self.driver.update_infra_instances_used_size()
#        self._validate_instances(expected_used_size=0)
#        self.assertListEqual(result['error'], [self.instance])
#        self.assertEqual(result['updated'], [])


@patch('drivers.mysqldb.MySQL.query', new=MagicMock(return_value=FAKE_QUERY_RESULT))
@patch('physical.models.DiskOffering.size_bytes', new=MagicMock(return_value=90))
class MySQLFOXHAUpdateUsedSizeTestCase(BaseMysqlDriverTestCase, BaseHAInstanceUpdateSizesTest):

    driver_class = MySQLFOXHA
    instances_quantity = 2

#    def setUp(self):
#        super(MySQLFOXHAUpdateUsedSizeTestCase, self).setUp()
#        instances = self._create_more_instances(3)
#        self._change_instance_type(instances[-2:], Instance.MYSQL)
#        self.instance.used_size_in_bytes = 0
#        self.instance.save()
#
#    def test_instance_alive(self, mock_query):
#        result = self.driver.update_infra_instances_used_size()
#        self._validate_instances()
#        self.assertListEqual(
#            result['updated'],
#            list(self.databaseinfra.instances.filter(instance_type=Instance.MYSQL))
#        )
#        self.assertEqual(result['error'], [])
#
#    def test_instance_dead(self, mock_query):
#        self.instance.status = Instance.DEAD
#        self.instance.save()
#        result = self.driver.update_infra_instances_used_size()
#
#        self.assertEqual(self.instance.used_size_in_bytes, 0)
#
#        alive_instances = list(self.databaseinfra.instances.filter(
#            status=Instance.ALIVE, instance_type=Instance.MYSQL
#        ))
#
#        self.assertEqual(alive_instances[0].used_size_in_bytes, 40)
#        self.assertListEqual(result['error'], [self.instance])
#        self.assertEqual(result['updated'], alive_instances)


class MySQLUsedAndTotalTestCase(BaseMysqlDriverTestCase):

    """
    Tests MySQL total and used
    """

    def test_masters_single_instance(self):
        """
            Test validates return total and used size when has single instance
        """
        self.driver.check_instance_is_master = MagicMock(
            side_effect=self.instance_helper.check_instance_is_master
        )
        self.instance.total_size_in_bytes = 105
        self.instance.used_size_in_bytes = 55
        self.instance.save()
        self.assertEqual(self.driver.masters_total_size_in_bytes, 105)
        self.assertEqual(self.driver.masters_used_size_in_bytes, 55)

    def test_masters_foxha_instance(self):
        """
            Test validates return total and used size when has single instance
        """
        self.driver = MySQLFOXHA(databaseinfra=self.databaseinfra)
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
        self.assertEqual(self.driver.masters_used_size_in_bytes, 10)


class MySQLEngineTestCase(BaseMysqlDriverTestCase):

    """
    Tests MySQL Engine
    """
    def setUp(self):
        super(MySQLEngineTestCase, self).setUp()

    def test_mysqldb_app_installed(self):
        self.assertTrue(DriverFactory.is_driver_available("mysql_single"))
        self.assertTrue(DriverFactory.is_driver_available("mysql_foxha"))

    # test mysql methods
    def test_instantiate_mysqldb_using_engine_factory(self):
        self.assertEqual(MySQL, type(self.driver))
        self.assertEqual(self.databaseinfra, self.driver.databaseinfra)

    def test_connection_string(self):
        self.assertEqual(
            "mysql://<user>:<password>@{}".format(self.infra_endpoint), self.driver.get_connection())

    def test_get_user(self):
        self.assertEqual(self.databaseinfra.user, self.driver.get_user())

    def test_get_password(self):
        self.assertEqual(
            self.databaseinfra.password, self.driver.get_password())

    def test_get_default_port(self):
        self.assertEqual(3306, self.driver.default_port)

    def test_connection_with_database(self):
        self.database = factory_logical.DatabaseFactory(
            name="my_db_url_name", databaseinfra=self.databaseinfra)
        self.assertEqual("mysql://<user>:<password>@{}/my_db_url_name".format(self.infra_endpoint),
                         self.driver.get_connection(database=self.database))


class ManageDatabaseMySQLTestCase(BaseMysqlDriverTestCase):

    """ Test case to managing database in mysql engine """

    def setUp(self):
        super(ManageDatabaseMySQLTestCase, self).setUp()
        self.database = factory_logical.DatabaseFactory(
            databaseinfra=self.databaseinfra)
        # ensure database is dropped
        # get fake driver
        self.instance.address = '127.0.0.1'
        self.instance.save()
        driver = self.databaseinfra.get_driver()
        driver.remove_database(self.database)

    def tearDown(self):
        if not Database.objects.filter(databaseinfra_id=self.databaseinfra.id):
            self.database.delete()
        super(ManageDatabaseMySQLTestCase, self).tearDown()

    def test_mysqldb_create_and_drop_database(self):
        LOG.debug("mysql_client: %s" % type(self.driver_client))
        # ensures database is removed
        try:
            self.driver.remove_database(self.database)
        except:
            pass
        self.assertFalse(self.database.name in self.driver.list_databases())
        self.driver.create_database(self.database)
        self.assertTrue(self.database.name in self.driver.list_databases())

        # drop database
        self.driver.remove_database(self.database)
        self.assertFalse(self.database.name in self.driver.list_databases())


class ManageCredentialsMySQLTestCase(BaseMysqlDriverTestCase):

    """ Test case to managing credentials in mysqldb engine """

    def setUp(self):
        super(ManageCredentialsMySQLTestCase, self).setUp()
        self.database = factory_logical.DatabaseFactory(
            databaseinfra=self.databaseinfra, name="test_mysql_credential")
        # ensures database doest not exists
        try:
            self.driver.remove_database(self.database)
        except:
            pass
        self.credential = factory_logical.CredentialFactory(
            database=self.database)
        self.driver.create_database(self.database)

    def tearDown(self):
        self.driver.remove_database(self.database)
        self.credential.delete()
        self.database.delete()
        super(ManageCredentialsMySQLTestCase, self).tearDown()

    def test_mysqldb_create__and_remove_credential(self):
        self.assertFalse(self.credential.user in self.driver.list_users())
        self.driver.create_user(self.credential)
        self.assertTrue(self.credential.user in self.driver.list_users())
        self.driver.remove_user(self.credential)
        self.assertFalse(self.credential.user in self.driver.list_users())
