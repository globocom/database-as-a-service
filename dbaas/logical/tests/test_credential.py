# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import mock
from django.test import TestCase
from physical.tests import factory as factory_physical
from drivers.fake import FakeDriver
from ..models import Credential
from . import factory as factory_logical


class CredentialTestCase(TestCase):

    def setUp(self):
        self.instance = factory_physical.InstanceFactory()
        self.databaseinfra = self.instance.databaseinfra
        self.database = factory_logical.DatabaseFactory(
            databaseinfra=self.databaseinfra)

    def tearDown(self):
        self.database.delete()

    def test_create_credential(self):

        credential = Credential.objects.create(
            user="super", password="super", database=self.database)

        self.assertTrue(credential.pk)

    def test_slugify_user_credential(self):

        credential = Credential.create_new_credential(
            user="a b c", database=self.database)

        self.assertTrue(credential.pk)
        self.assertEqual(credential.user, 'a_b_c')

    def test_underscore_in_slugged_user_credential(self):

        credential = Credential.objects.create(
            user="a_b_c_d", password="super", database=self.database)

        self.assertTrue(credential.pk)
        self.assertEqual(credential.user, "a_b_c_d")

    def test_cannot_edit_user_credential(self):

        credential = factory_logical.CredentialFactory(database=self.database)

        self.assertTrue(credential.pk)

        credential.user = "super3"

        self.assertRaises(AttributeError, credential.save)

    def test_cannot_edit_database_credential(self):

        credential = factory_logical.CredentialFactory(database=self.database)
        another_database = factory_logical.DatabaseFactory(
            databaseinfra=self.databaseinfra)

        credential.database = another_database

        self.assertRaises(AttributeError, credential.save)

    @mock.patch.object(FakeDriver, 'remove_user')
    def test_delete_model_remove_credentials_from_driver(self, remove_user):

        credential = factory_logical.CredentialFactory()
        credential.delete()
        remove_user.assert_called_once_with(credential)
