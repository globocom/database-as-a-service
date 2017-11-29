# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from mock import MagicMock
import logging
from drivers import DriverFactory
from drivers.tests.base import BaseDriverTestCase
from physical.tests import factory as factory_physical
from logical.tests import factory as factory_logical
from logical.models import Database
from ..mysqldb import MySQL, MySQLFOXHA
from django.conf import settings

LOG = logging.getLogger(__name__)


class AbstractTestDriverMysql(BaseDriverTestCase):

    host = settings.DB_HOST
    port = 3306
    db_user = 'root'
    db_password = settings.DB_PASSWORD
    engine_name = 'mysql'
    instance_type = 1
    driver_class = MySQL
    driver_client_lookup = '__mysql_client__'

#    def setUp(self):
#        self.mysql_host = '127.0.0.1'
#        self.mysql_port = settings.DB_PORT or 3306
#        self.mysql_endpoint = '{}:{}'.format(self.mysql_host, self.mysql_port)
#        self.databaseinfra = factory_physical.DatabaseInfraFactory(
#            engine__engine_type__name='mysql', user="root",
#            password=settings.DB_PASSWORD, endpoint=self.mysql_endpoint)
#        self.instance = factory_physical.InstanceFactory(
#            databaseinfra=self.databaseinfra, address=self.mysql_host,
#            port=self.mysql_port, instance_type=1)
#        self.driver = MySQL(databaseinfra=self.databaseinfra)
#        self._mysql_client = None
#
#    def tearDown(self):
#        if not Database.objects.filter(databaseinfra_id=self.databaseinfra.id):
#            self.databaseinfra.delete()
#        if self._mysql_client:
#            self._mysql_client.close()
#        self.driver = self.databaseinfra = self._mysql_client = None

    @property
    def mysql_client(self):
        return self._driver_client


class MySQLUsedAndTotalTestCase(AbstractTestDriverMysql):

    """
    Tests MySQL total and used
    """

    def setUp(self):
        super(MySQLUsedAndTotalTestCase, self).setUp()
        self.masters_quantity = 1
        self.instance.address = '127.0.0.1'
        self.instance.save()
        self.driver.check_instance_is_master = MagicMock(
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
                address='127.{0}.{0}.{0}'.format(n), port=self.port,
                instance_type=self.instance_type, total_size_in_bytes=total_size_in_bytes
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

    def test_masters_foxha_instance(self):
        """
            Test validates return total and used size when has single instance
        """
        self.driver = MySQLFOXHA(databaseinfra=self.databaseinfra)
        self.driver.check_instance_is_master = MagicMock(
            side_effect=self._check_instance_is_master
        )
        self._create_more_instances()
        self.instance.total_size_in_bytes = 35
        self.instance.used_size_in_bytes = 10
        self.instance.save()
        self.assertEqual(self.driver.masters_total_size_in_bytes, 35)
        self.assertEqual(self.driver.masters_used_size_in_bytes, 10)


class MySQLEngineTestCase(AbstractTestDriverMysql):

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
            "mysql://<user>:<password>@{}".format(self.endpoint), self.driver.get_connection())

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
        self.assertEqual("mysql://<user>:<password>@{}/my_db_url_name".format(self.endpoint),
                         self.driver.get_connection(database=self.database))


class ManageDatabaseMySQLTestCase(AbstractTestDriverMysql):

    """ Test case to managing database in mysql engine """

    def setUp(self):
        super(ManageDatabaseMySQLTestCase, self).setUp()
        self.database = factory_logical.DatabaseFactory(
            databaseinfra=self.databaseinfra)
        # ensure database is dropped
        # get fake driver
        driver = self.databaseinfra.get_driver()
        driver.remove_database(self.database)

    def tearDown(self):
        if not Database.objects.filter(databaseinfra_id=self.databaseinfra.id):
            self.database.delete()
        super(ManageDatabaseMySQLTestCase, self).tearDown()

    def test_mysqldb_create_and_drop_database(self):
        LOG.debug("mysql_client: %s" % type(self.mysql_client))
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


class ManageCredentialsMySQLTestCase(AbstractTestDriverMysql):

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
