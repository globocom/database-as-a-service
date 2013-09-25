# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.test.client import Client
from django.test import TestCase
from django.test.client import RequestFactory
from django.db import IntegrityError

from ..models import Database, Credential

from base.tests import factory
from base.engine import base


class FakeEngine(base.BaseEngine):
    
    def get_connection(self):
        return CONNECTION_TEST

class DatabaseTestCase(TestCase):

    def setUp(self):
        self.instance = factory.InstanceFactory()
        self.engine = FakeEngine(instance=self.instance)
        self.database = Database.objects.create(name="super", instance=self.instance)

    def tearDown(self):
        self.database.delete()
        self.instance.delete()
        self.instance = self.engine = None

    def test_create_credential(self):
        
        credential = Credential.objects.create(user="super", password="super", database=self.database)
        
        self.assertTrue(credential.id)
        credential.delete()

    def test_slugify_user_credential(self):
        
        credential = Credential.objects.create(user="a b c", password="super", database=self.database)
        
        self.assertTrue(credential.id)
        self.assertEqual(credential.user, 'a_b_c')
        credential.delete()


    def test_underscore_in_slugged_user_credential(self):
        
        credential = Credential.objects.create(user="a_b_c_d", password="super", database=self.database)
        
        self.assertTrue(credential.id)
        self.assertEqual(credential.user, "a_b_c_d")
        credential.delete()

    def test_cannot_edit_user_credential(self):
        
        credential = Credential.objects.create(user="super2", password="super2", database=self.database)
        
        self.assertTrue(credential.id)
        
        credential.user = "super3"
        
        self.assertRaises(AttributeError, credential.save)
        credential.delete()

    def test_cannot_edit_database_credential(self):
        
        credential = Credential.objects.create(user="super4", password="super4", database=self.database)
        database = Database.objects.create(name="oxente", instance=self.instance)
        
        credential.database = database
        
        self.assertRaises(AttributeError, credential.save)
        database.delete()
        credential.delete()
