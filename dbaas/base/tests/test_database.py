# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.test import TestCase

from ..models import Database

from base.tests import factory
from base.engine import base


class FakeEngine(base.BaseEngine):
    
    def get_connection(self):
        return "a"

class DatabaseTestCase(TestCase):

    def setUp(self):
        self.instance = factory.InstanceFactory()
        self.engine = FakeEngine(instance=self.instance)

    def tearDown(self):
        self.instance.delete()
        self.instance = self.engine = None

    def test_create_database(self):
        
        database = Database.objects.create(name="super", instance=self.instance)

        self.assertTrue(database.id)
        database.delete()

    def test_slugify_database_name(self):
        
        database = Database.objects.create(name="w h a t", instance=self.instance)
        
        self.assertTrue(database.id)
        self.assertEqual(database.name, 'w_h_a_t')
        database.delete()

    def test_cannot_edit_database_name(self):
        
        database = Database.objects.create(name="super2", instance=self.instance)
        
        self.assertTrue(database.id)
        
        database.name = "super3"
        
        self.assertRaises(AttributeError, database.save)
        database.delete()



