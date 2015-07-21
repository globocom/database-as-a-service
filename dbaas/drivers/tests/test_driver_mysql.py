# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import mock
import logging
from django.test import TestCase
from drivers import DriverFactory
from physical.tests import factory as factory_physical
from logical.tests import factory as factory_logical
from logical.models import Database
from ..mysqldb import MySQL
from django.conf import settings

LOG = logging.getLogger(__name__)


class AbstractTestDriverMysql(TestCase):

    def setUp(self):
        self.databaseinfra = factory_physical.DatabaseInfraFactory(
            user="root", password=settings.DB_PASSWORD, endpoint="127.0.0.1:3306")
        self.instance = factory_physical.InstanceFactory(
            databaseinfra=self.databaseinfra, port=3306)
        self.driver = MySQL(databaseinfra=self.databaseinfra)
        self._mysql_client = None

    def tearDown(self):
        if not Database.objects.filter(databaseinfra_id=self.databaseinfra.id):
            self.databaseinfra.delete()
        if self._mysql_client:
            self._mysql_client.close()
        self.driver = self.databaseinfra = self._mysql_client = None

    @property
    def mysql_client(self):
        if self._mysql_client is None:
            self._mysql_client = self.driver.__mysql_client__(self.instance)
        return self._mysql_client


class MySQLEngineTestCase(AbstractTestDriverMysql):

    """
    Tests MySQL Engine
    """

    def test_mysqldb_app_installed(self):
        self.assertTrue(DriverFactory.is_driver_available("mysqldb"))

    # test mysql methods
    def test_instantiate_mysqldb_using_engine_factory(self):
        self.assertEqual(MySQL, type(self.driver))
        self.assertEqual(self.databaseinfra, self.driver.databaseinfra)

    def test_connection_string(self):
        self.assertEqual(
            "mysql://<user>:<password>@127.0.0.1:3306", self.driver.get_connection())

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
        self.assertEqual("mysql://<user>:<password>@127.0.0.1:3306/my_db_url_name",
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
