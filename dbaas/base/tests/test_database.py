# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.test.client import Client
from django.test import TestCase
from django.test.client import RequestFactory
from django.db import IntegrityError

from ..models import Database

from base.tests import factory
from base.engine import base


class FakeEngine(base.BaseEngine):
    
    def get_connection(self):
        return CONNECTION_TEST

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

    def test_create_duplicate_database_error(self):
        
        database = Database.objects.create(name="super", instance=self.instance)
        
        self.assertTrue(database.id)
        
        self.assertRaises(IntegrityError, Database.objects.create, name="super", instance=self.instance)

    def test_slugify_database_name(self):
        
        database = Database.objects.create(name="w h a t", instance=self.instance)
        
        self.assertTrue(database.id)
        self.assertEqual(database.name, 'w_h_a_t')
        
        database2 = Database.objects.create(name="w.h.e.r.e", instance=self.instance)
        
        self.assertTrue(database2.id)
        self.assertEqual(database2.name, 'w_h_e_r_e')

    def test_cannot_edit_database_name(self):
        
        database = Database.objects.create(name="super2", instance=self.instance)
        
        self.assertTrue(database.id)
        
        database.name = "super3"
        
        self.assertRaises(AttributeError, database.save)



