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
from unittest import skip

LOG = logging.getLogger(__name__)


class FakeDriver(base.BaseDriver):

    def get_connection(self):
        return 'connection-url'


class DatabaseTestCase(TestCase):

    def setUp(self):
        self.instance = physical_factory.InstanceFactory()
        self.databaseinfra = self.instance.databaseinfra
        self.engine = FakeDriver(databaseinfra=self.databaseinfra)
        self.environment = physical_factory.EnvironmentFactory()

    def tearDown(self):
        self.engine = None

    def test_create_database(self):

        database = Database(name="blabla", databaseinfra=self.databaseinfra,
                            environment=self.environment)
        database.save()

        self.assertTrue(database.pk)

    @skip("aovid this test due to region migration")
    def test_create_duplicate_database_error(self):

        database = Database(name="bleble", databaseinfra=self.databaseinfra,
                            environment=self.environment)

        database.save()

        self.assertTrue(database.pk)

        self.assertRaises(IntegrityError, Database(name="bleble",
                                                   databaseinfra=self.databaseinfra).save)

    def test_slugify_database_name_with_spaces(self):

        database = factory.DatabaseFactory.build(name="w h a t",
                                                 databaseinfra=self.databaseinfra,
                                                 environment=self.environment)

        database.full_clean()
        database.save()
        self.assertTrue(database.id)
        self.assertEqual(database.name, 'w_h_a_t')

    def test_slugify_database_name_with_dots(self):
        database = factory.DatabaseFactory.build(name="w.h.e.r.e",
                                                 databaseinfra=self.databaseinfra,
                                                 environment=self.environment)

        database.full_clean()
        database.save()
        self.assertTrue(database.id)
        self.assertEqual(database.name, 'w_h_e_r_e')

    def test_cannot_edit_database_name(self):

        database = factory.DatabaseFactory(name="w h a t",
                                           databaseinfra=self.databaseinfra,
                                           environment=self.environment)

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
        database = factory.DatabaseFactory(name="db1cache",
                                           databaseinfra=self.databaseinfra,
                                           environment=self.environment)
        self.assertIsNotNone(database.database_status)
        self.assertEqual(
            [mock.call(), mock.call(force_refresh=True)], get_info.call_args_list)

    '''

    @mock.patch.object(clone_database, 'delay')
    def test_database_clone(self, delay):

        database = Database(name="morpheus", databaseinfra=self.databaseinfra)

        database.save()

        self.assertTrue(database.pk)

        clone_name = "morpheus_clone"
        Database.clone(database, clone_name, None)

        clone_database = Database.objects.get(name=clone_name)

        self.assertTrue(clone_database.pk)
        self.assertEqual(clone_database.name, clone_name)
        self.assertEqual(clone_database.project, database.project)
        self.assertEqual(clone_database.team, database.team)

        credential = clone_database.credentials.all()[0]

        self.assertEqual(credential.user, "u_morpheus_clone")

    @mock.patch.object(clone_database, 'delay')
    def test_database_clone_with_white_space(self, delay):
        """Tests that a clone database created with white spaces passes the test"""

        database = Database(name="trinity", databaseinfra=self.databaseinfra)

        database.save()

        self.assertTrue(database.pk)

        clone_name = "trinity clone"
        Database.clone(database, clone_name, None)

        clone_database = Database.objects.get(name="trinity_clone")

        self.assertTrue(clone_database.pk)
        self.assertEqual(clone_database.name, "trinity_clone")
        self.assertEqual(clone_database.project, database.project)
        self.assertEqual(clone_database.team, database.team)

        credential = clone_database.credentials.all()[0]

        self.assertEqual(credential.user, "u_trinity_clone")

    '''
