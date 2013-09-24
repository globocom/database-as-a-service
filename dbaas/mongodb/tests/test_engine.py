# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import mock
from hamcrest import has_entries
from hamcrest.library.integration import match_equality
from django.test import TestCase
from base.engine.factory import EngineFactory
from base.tests import factory
from ..engine import MongoDB

class MongoDBEngineTestCase(TestCase):
    """
    Tests MongoDB Engine
    """

    def setUp(self):
        self.instance = factory.InstanceFactory()
        self.engine = MongoDB(instance=self.instance)

    def tearDown(self):
        self.instance.delete()
        self.engine = self.instance = None

    def test_mongodb_app_installed(self):
        self.assertTrue(EngineFactory.is_engine_available("mongodb")) 

    #test mongo methods
    def test_instantiate_mongodb_using_engine_factory(self):
        mongodb_engine = EngineFactory.factory(self.instance)
        self.assertEqual(MongoDB, type(mongodb_engine))
        self.assertEqual(self.instance, mongodb_engine.instance)

    def test_connection_string(self):
        self.assertEqual("%s:%s" % (self.instance.node.address, self.instance.node.port), self.engine.get_connection())

    def test_get_user(self):
        self.assertEqual(self.instance.user, self.engine.get_user())

    def test_get_password(self):
        self.assertEqual(self.instance.password, self.engine.get_password())

    def test_mongodb_status(self):
        self.assertRaises(NotImplementedError, self.engine.status)


class ManageDatabaseMongoDBTestCase(TestCase):
    """ Test case to managing database in mongodb engine """

    def setUp(self):
        self.instance = factory.InstanceFactory()
        self.database = factory.DatabaseFactory(instance=self.instance)
        self.credential = factory.CredentialFactory(database=self.database)
        self.engine = MongoDB(instance=self.instance)

    def tearDown(self):
        self.credential.delete()
        self.database.delete()
        self.instance.delete()
        self.engine = self.instance = self.credential = self.database = None

    @mock.patch.object(MongoDB, 'call_script')
    def test_mongodb_create_database(self, call_script):
        self.engine.create_database(self.database)
        required_envs={
            "INSTANCE_CONNECTION": self.engine.get_connection(),
            "INSTANCE_USER": self.engine.get_user(),
            "INSTANCE_PASSWORD": self.engine.get_password(),
            "DATABASE_NAME": self.database.name,
        }
        call_script.assert_called_once_with(MongoDB.SCRIPT, ['createdatabase'], envs=match_equality(has_entries(required_envs)))

    @mock.patch.object(MongoDB, 'call_script')
    def test_mongodb_remove_database(self, call_script):
        self.engine.remove_database(self.database)
        required_envs={
            "INSTANCE_CONNECTION": self.engine.get_connection(),
            "INSTANCE_USER": self.engine.get_user(),
            "INSTANCE_PASSWORD": self.engine.get_password(),
            "DATABASE_NAME": self.database.name,
        }
        call_script.assert_called_once_with(MongoDB.SCRIPT, ['dropdatabase'], envs=match_equality(has_entries(required_envs)))


class ManageCredentialsMongoDBTestCase(TestCase):
    """ Test cases for managing credentials in mongodb engine """

    def setUp(self):
        self.instance = factory.InstanceFactory()
        self.database = factory.DatabaseFactory(instance=self.instance)
        self.credential = factory.CredentialFactory(database=self.database)
        self.engine = MongoDB(instance=self.instance)

    def tearDown(self):
        self.credential.delete()
        self.database.delete()
        self.instance.delete()
        self.engine = self.instance = self.credential = self.database = None

    @mock.patch.object(MongoDB, 'call_script')
    def test_mongodb_create_user(self, call_script):
        self.engine.create_user(self.credential)
        required_envs={
            "INSTANCE_CONNECTION": self.engine.get_connection(),
            "INSTANCE_USER": self.engine.get_user(),
            "INSTANCE_PASSWORD": self.engine.get_password(),
            "DATABASE_NAME": self.database.name,
            "CREDENTIAL_USER": self.credential.user,
            "CREDENTIAL_PASSWORD": self.credential.password,
        }
        call_script.assert_called_once_with(MongoDB.SCRIPT, ['adduser'], envs=match_equality(has_entries(required_envs)))

    @mock.patch.object(MongoDB, 'call_script')
    def test_mongodb_remove_user(self, call_script):
        self.engine.remove_user(self.credential)
        required_envs={
            "INSTANCE_CONNECTION": self.engine.get_connection(),
            "INSTANCE_USER": self.engine.get_user(),
            "INSTANCE_PASSWORD": self.engine.get_password(),
            "DATABASE_NAME": self.database.name,
            "CREDENTIAL_USER": self.credential.user,
            "CREDENTIAL_PASSWORD": self.credential.password,
        }
        call_script.assert_called_once_with(MongoDB.SCRIPT, ['dropuser'], envs=match_equality(has_entries(required_envs)))


