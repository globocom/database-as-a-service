# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.test.client import Client
from django.test import TestCase
from django.test.client import RequestFactory
from django.db import IntegrityError

from ..models import Database, Credential

from base.tests import factory
from base.driver import base


class FakeDriver(base.BaseDriver):

    def get_connection(self):
        return CONNECTION_TEST

class DatabaseTestCase(TestCase):

    def setUp(self):
        self.instance = factory.InstanceFactory()
        self.engine = FakeDriver(instance=self.instance)
        self.database = Database.objects.create(name="super", instance=self.instance)

    def tearDown(self):
        self.engine = None
        self.database.delete()

    def test_create_credential(self):

        credential = Credential.objects.create(user="super", password="super", database=self.database)

        self.assertTrue(credential.id)

    def test_slugify_user_credential(self):

        credential = Credential.objects.create(user="a b c", password="super", database=self.database)

        self.assertTrue(credential.id)
        self.assertEqual(credential.user, 'a_b_c')


    def test_underscore_in_slugged_user_credential(self):

        credential = Credential.objects.create(user="a_b_c_d", password="super", database=self.database)

        self.assertTrue(credential.id)
        self.assertEqual(credential.user, "a_b_c_d")

    def test_cannot_edit_user_credential(self):

        credential = Credential.objects.create(user="super2", password="super2", database=self.database)

        self.assertTrue(credential.id)

        credential.user = "super3"

        self.assertRaises(AttributeError, credential.save)

    def test_cannot_edit_database_credential(self):

        credential = Credential.objects.create(user="super4", password="super4", database=self.database)
        database = Database.objects.create(name="oxente", instance=self.instance)

        credential.database = database

        self.assertRaises(AttributeError, credential.save)
