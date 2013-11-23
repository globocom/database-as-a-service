# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import mock
from django.test import TestCase
from django.db import IntegrityError
from . import factory
from physical.tests import factory as physical_factory
from ..models import Database
from physical.models import DatabaseInfra
from drivers import base

import logging

LOG = logging.getLogger(__name__)


class FakeDriver(base.BaseDriver):
    
    def get_connection(self):
        return 'connection-url'


class DatabaseTestCase(TestCase):

    def setUp(self):
        self.instance = physical_factory.InstanceFactory()
        self.databaseinfra = self.instance.databaseinfra
        self.engine = FakeDriver(databaseinfra=self.databaseinfra)

    def tearDown(self):
        self.engine = None

    def test_create_database(self):
        
        database = Database(name="blabla", databaseinfra=self.databaseinfra)
        database.save()
        
        self.assertTrue(database.pk)
        

    def test_create_duplicate_database_error(self):
        
        database = Database(name="bleble", databaseinfra=self.databaseinfra)
        
        database.save()
        
        self.assertTrue(database.pk)
        
        self.assertRaises(IntegrityError, Database(name="bleble", databaseinfra=self.databaseinfra).save)

    def test_slugify_database_name_with_spaces(self):
        
        database = factory.DatabaseFactory.build(name="w h a t", databaseinfra=self.databaseinfra)
        
        database.full_clean()
        database.save()
        self.assertTrue(database.id)
        self.assertEqual(database.name, 'w_h_a_t')
        
    def test_slugify_database_name_with_dots(self):
        database = factory.DatabaseFactory.build(name="w.h.e.r.e", databaseinfra=self.databaseinfra)
        
        database.full_clean()
        database.save()
        self.assertTrue(database.id)
        self.assertEqual(database.name, 'w_h_e_r_e')
    
    def test_cannot_edit_database_name(self):
        
        database = factory.DatabaseFactory(name="w h a t", databaseinfra=self.databaseinfra)
        
        self.assertTrue(database.id)
        
        database.name = "super3"
        
        self.assertRaises(AttributeError, database.save)

    @mock.patch.object(DatabaseInfra, 'get_info')
    def test_new_database_bypass_datainfra_info_cache(self, get_info):
        def side_effect_get_info(force_refresh=False):
            m = mock.Mock()
            if not force_refresh:
                m.get_database_status.return_value = None
                return m
            m.get_database_status.return_value = object()
            return m

        get_info.side_effect = side_effect_get_info
        database = factory.DatabaseFactory(name="db1cache", databaseinfra=self.databaseinfra)
        self.assertIsNotNone(database.database_status)
        self.assertEqual([mock.call(), mock.call(force_refresh=True)], get_info.call_args_list)
