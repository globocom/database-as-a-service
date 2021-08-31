# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.test import TestCase
from ..models import DatabaseUpgrade
from .factory import DatabaseMigrageFactoryStageZero


class DatabaseMigrateTestCase(TestCase):

    def setUp(self):
        self.database_migrate = DatabaseMigrageFactoryStageZero()

    def tearDown(self):
        self.database_migrate.delete()

    def test_update_step(self):
        self.assertIsNone(self.database_migrate.started_at)
        self.assertEqual(self.database_migrate.status, DatabaseUpgrade.WAITING)
        self.assertEqual(self.database_migrate.current_step, 0)

        self.database_migrate.update_step(1)
        self.assertIsNotNone(self.database_migrate.started_at)
        self.assertEqual(self.database_migrate.status, DatabaseUpgrade.RUNNING)
        self.assertEqual(self.database_migrate.current_step, 1)

        started_at_first = self.database_migrate.started_at
        self.database_migrate.update_step(2)
        self.assertEqual(self.database_migrate.started_at, started_at_first)
        self.assertEqual(self.database_migrate.status, DatabaseUpgrade.RUNNING)
        self.assertEqual(self.database_migrate.current_step, 2)

        self.assertEqual(self.database_migrate.migration_stage, 0)
