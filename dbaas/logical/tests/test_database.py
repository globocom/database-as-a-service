# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.test import TestCase
from django.db import IntegrityError
from . import factory
from ..models import Database
from drivers import base


class FakeDriver(base.BaseDriver):
    
    def get_connection(self):
        return 'connection-url'


class DatabaseTestCase(TestCase):

    def setUp(self):
        self.node = factory.NodeFactory()
        self.instance = self.node.instance
        self.engine = FakeDriver(instance=self.instance)

    def tearDown(self):
        self.engine = None

    def test_create_database(self):
        
        database = Database(name="blabla", instance=self.instance)
        database.save()
        
        self.assertTrue(database.pk)
        

    def test_create_duplicate_database_error(self):
        
        database = Database(name="bleble", instance=self.instance)
        
        database.save()
        
        self.assertTrue(database.pk)
        
        self.assertRaises(IntegrityError, Database(name="bleble", instance=self.instance).save)

    def test_slugify_database_name(self):
        
        database = factory.DatabaseFactory(name="w h a t", instance=self.instance)
        
        self.assertTrue(database.id)
        self.assertEqual(database.name, 'w_h_a_t')
        
        database2 = factory.DatabaseFactory(name="w.h.e.r.e", instance=self.instance)
        
        self.assertTrue(database2.id)
        self.assertEqual(database2.name, 'w_h_e_r_e')
    
    def test_cannot_edit_database_name(self):
        
        database = factory.DatabaseFactory(name="w h a t", instance=self.instance)
        
        self.assertTrue(database.id)
        
        database.name = "super3"
        
        self.assertRaises(AttributeError, database.save)



