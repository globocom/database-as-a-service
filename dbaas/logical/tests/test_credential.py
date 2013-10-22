# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.test import TestCase
from physical.tests import factory as factory_physical
from drivers import base
from ..models import Credential
from . import factory as factory_logical


class FakeDriver(base.BaseDriver):

    def get_connection(self):
        return 'connection-url'

class CredentialTestCase(TestCase):

    def setUp(self):
        self.node = factory_physical.NodeFactory()
        self.instance = self.node.instance
        self.engine = FakeDriver(instance=self.instance)
        self.database = factory_logical.DatabaseFactory(instance=self.instance)

    def tearDown(self):
        self.engine = None
        self.database.delete()

    def test_create_credential(self):

        credential = Credential.objects.create(user="super", password="super", database=self.database)

        self.assertTrue(credential.pk)

    def test_slugify_user_credential(self):

        credential = Credential.objects.create(user="a b c", password="super", database=self.database)

        self.assertTrue(credential.pk)
        self.assertEqual(credential.user, 'a_b_c')


    def test_underscore_in_slugged_user_credential(self):

        credential = Credential.objects.create(user="a_b_c_d", password="super", database=self.database)

        self.assertTrue(credential.pk)
        self.assertEqual(credential.user, "a_b_c_d")

    def test_cannot_edit_user_credential(self):

        credential = factory_logical.CredentialFactory(database=self.database)

        self.assertTrue(credential.pk)

        credential.user = "super3"

        self.assertRaises(AttributeError, credential.save)

    def test_cannot_edit_database_credential(self):

        credential = factory_logical.CredentialFactory(database=self.database)
        another_database = factory_logical.DatabaseFactory()

        credential.database = another_database

        self.assertRaises(AttributeError, credential.save)
