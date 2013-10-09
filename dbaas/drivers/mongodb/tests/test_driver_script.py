# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import mock
import unittest
from hamcrest import has_entries
from hamcrest.library.integration import match_equality
from django.test import TestCase
from ... import DriverFactory, AuthenticationError, ErrorRunningScript, ConnectionError
from physical.tests import factory as factory_physical
from logical.tests import factory as factory_logical
from ..driver_script import MongoDBScript as MongoDB


@unittest.skip('Using test_driver_pymongo')
class MongoDBScriptEngineTestCase(TestCase):
    """
    Tests MongoDB Engine
    """

    def setUp(self):
        self.instance = factory_physical.InstanceFactory()
        self.driver = MongoDB(instance=self.instance)

    def tearDown(self):
        self.instance.delete()
        self.driver = self.instance = None

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


@unittest.skip('Using test_driver_pymongo')
class ManageDatabaseMongoDBScriptTestCase(TestCase):
    """ Test case to managing database in mongodb engine """

    def setUp(self):
        self.instance = factory_physical.InstanceFactory()
        self.database = factory_logical.DatabaseFactory(instance=self.instance)
        self.credential = factory_logical.CredentialFactory(database=self.database)
        self.driver = MongoDB(instance=self.instance)

    def tearDown(self):
        self.credential.delete()
        self.database.delete()
        self.instance.delete()
        self.driver = self.instance = self.credential = self.database = None

    @mock.patch.object(MongoDB, 'call_script')
    def test_mongodb_create_database(self, call_script):
        self.driver.create_database(self.database)
        required_envs={
            "INSTANCE_CONNECTION": self.driver.get_connection(),
            "INSTANCE_USER": self.driver.get_user(),
            "INSTANCE_PASSWORD": self.driver.get_password(),
            "DATABASE_NAME": self.database.name,
        }
        call_script.assert_called_once_with(MongoDB.SCRIPT, ['createdatabase'], envs=match_equality(has_entries(required_envs)))

    @mock.patch.object(MongoDB, 'call_script')
    def test_mongodb_remove_database(self, call_script):
        self.driver.remove_database(self.database)
        required_envs={
            "INSTANCE_CONNECTION": self.driver.get_connection(),
            "INSTANCE_USER": self.driver.get_user(),
            "INSTANCE_PASSWORD": self.driver.get_password(),
            "DATABASE_NAME": self.database.name,
        }
        call_script.assert_called_once_with(MongoDB.SCRIPT, ['dropdatabase'], envs=match_equality(has_entries(required_envs)))


@unittest.skip('Using test_driver_pymongo')
class ManageCredentialsMongoDBScriptTestCase(TestCase):
    """ Test cases for managing credentials in mongodb engine """

    def setUp(self):
        self.instance = factory_physical.InstanceFactory()
        self.database = factory_logical.DatabaseFactory(instance=self.instance)
        self.credential = factory_logical.CredentialFactory(database=self.database)
        self.driver = MongoDB(instance=self.instance)

    def tearDown(self):
        self.credential.delete()
        self.database.delete()
        self.instance.delete()
        self.driver = self.instance = self.credential = self.database = None

    @mock.patch.object(MongoDB, 'call_script')
    def test_mongodb_create_user(self, call_script):
        self.driver.create_user(self.credential)
        required_envs={
            "INSTANCE_CONNECTION": self.driver.get_connection(),
            "INSTANCE_USER": self.driver.get_user(),
            "INSTANCE_PASSWORD": self.driver.get_password(),
            "DATABASE_NAME": self.database.name,
            "CREDENTIAL_USER": self.credential.user,
            "CREDENTIAL_PASSWORD": self.credential.password,
        }
        call_script.assert_called_once_with(MongoDB.SCRIPT, ['adduser'], envs=match_equality(has_entries(required_envs)))

    @mock.patch.object(MongoDB, 'call_script')
    def test_mongodb_remove_user(self, call_script):
        self.driver.remove_user(self.credential)
        required_envs={
            "INSTANCE_CONNECTION": self.driver.get_connection(),
            "INSTANCE_USER": self.driver.get_user(),
            "INSTANCE_PASSWORD": self.driver.get_password(),
            "DATABASE_NAME": self.database.name,
            "CREDENTIAL_USER": self.credential.user,
            "CREDENTIAL_PASSWORD": self.credential.password,
        }
        call_script.assert_called_once_with(MongoDB.SCRIPT, ['dropuser'], envs=match_equality(has_entries(required_envs)))



@unittest.skip('Using test_driver_pymongo')
class StatusAndInfoMongoDBScriptTestCase(TestCase):
    """ Test cases for get status and informations from mongodb """

    def setUp(self):
        self.instance = factory_physical.InstanceFactory()
        self.driver = MongoDB(instance=self.instance)

    def tearDown(self):
        pass

    @mock.patch.object(MongoDB, 'call_script')
    def test_check_status_will_raises_connection_error(self, call_script):
        def raise_error(*a, **kw):
            raise ErrorRunningScript(script_name=MongoDB.SCRIPT, exit_code=1, stdout="Error: couldn't connect to server xxx:yyy at src/mongo/shell/mongo.js:147")
        call_script.side_effect = raise_error
        self.assertRaises(ConnectionError, self.driver.check_status)
        required_envs={
            "INSTANCE_CONNECTION": self.driver.get_connection(),
            "INSTANCE_USER": self.driver.get_user(),
            "INSTANCE_PASSWORD": self.driver.get_password(),
        }
        call_script.assert_called_once_with(MongoDB.SCRIPT, ["status"], envs=match_equality(has_entries(required_envs)))

    @mock.patch.object(MongoDB, 'call_script')
    def test_check_status_will_raises_authentication_error(self, call_script):
        def raise_error(*a, **kw):
            raise ErrorRunningScript(script_name=MongoDB.SCRIPT, exit_code=1, stdout="Error: 18 { code: 18, ok: 0.0, errmsg: \"auth fails\" }")
        call_script.side_effect = raise_error
        self.assertRaises(AuthenticationError, self.driver.check_status)
        required_envs={
            "INSTANCE_CONNECTION": self.driver.get_connection(),
            "INSTANCE_USER": self.driver.get_user(),
            "INSTANCE_PASSWORD": self.driver.get_password(),
        }
        call_script.assert_called_once_with(MongoDB.SCRIPT, ["status"], envs=match_equality(has_entries(required_envs)))

    @mock.patch.object(MongoDB, 'call_script')
    def test_mongodb_create_user(self, call_script):
        database_base1 = factory_logical.DatabaseFactory(instance=self.instance, name="base1")

        results = [
            '  { "host": "xxx", \n"version": "2.4.6", "localTime" : ISODate("2013-09-26T20:47:56.766Z") } ',
            ' { "databases": [ { "name": "base1", "sizeOnDisk": 67108864 } ], "totalSize": 100663296 } '
        ]
        def sequence_calls(*a, **kw):
            return results.pop(0)

        call_script.side_effect = sequence_calls
        instance_status = self.driver.info()
        required_envs={
            "INSTANCE_CONNECTION": self.driver.get_connection(),
            "INSTANCE_USER": self.driver.get_user(),
            "INSTANCE_PASSWORD": self.driver.get_password(),
        }
        call_script.assert_any_call(MongoDB.SCRIPT, ["serverstatus"], envs=match_equality(has_entries(required_envs)))
        call_script.assert_any_call(MongoDB.SCRIPT, ["listdatabases"], envs=match_equality(has_entries(required_envs)))
        self.assertEquals("2.4.6", instance_status.version)
        self.assertEquals(100663296, instance_status.size_in_bytes)
        self.assertEquals(96, instance_status.size_in_mb)
        self.assertEquals(0.09375, instance_status.size_in_gb)

        base1_status = instance_status.get_database_status("base1")
        self.assertEquals(database_base1, base1_status.database_model)
        self.assertEquals(67108864, base1_status.size_in_bytes)

