# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.test import TestCase
from ..models import DatabaseUpgrade
from .factory import DatabaseUpgradeFactory


class DatabaseUpgradeTestCase(TestCase):

    def setUp(self):
        self.database_upgrade = DatabaseUpgradeFactory()

    def tearDown(self):
        self.database_upgrade.delete()

    def test_update_step(self):
        self.assertIsNone(self.database_upgrade.started_at)
        self.assertEqual(self.database_upgrade.status, DatabaseUpgrade.WAITING)
        self.assertEqual(self.database_upgrade.current_step, 0)

        self.database_upgrade.update_step(1)
        self.assertIsNotNone(self.database_upgrade.started_at)
        self.assertEqual(self.database_upgrade.status, DatabaseUpgrade.RUNNING)
        self.assertEqual(self.database_upgrade.current_step, 1)

        started_at_first = self.database_upgrade.started_at
        self.database_upgrade.update_step(2)
        self.assertEqual(self.database_upgrade.started_at, started_at_first)
        self.assertEqual(self.database_upgrade.status, DatabaseUpgrade.RUNNING)
        self.assertEqual(self.database_upgrade.current_step, 2)

    def test_status_error(self):
        self.assertIsNone(self.database_upgrade.finished_at)
        self.assertEqual(self.database_upgrade.status, DatabaseUpgrade.WAITING)

        self.database_upgrade.set_error()
        self.assertIsNotNone(self.database_upgrade.finished_at)
        self.assertEqual(self.database_upgrade.status, DatabaseUpgrade.ERROR)

    def test_status_success(self):
        self.assertIsNone(self.database_upgrade.finished_at)
        self.assertEqual(self.database_upgrade.status, DatabaseUpgrade.WAITING)

        self.database_upgrade.set_success()
        self.assertIsNotNone(self.database_upgrade.finished_at)
        self.assertEqual(self.database_upgrade.status, DatabaseUpgrade.SUCCESS)

    def test_is_status_error(self):
        self.assertFalse(self.database_upgrade.is_status_error)

        self.database_upgrade.set_error()
        self.assertTrue(self.database_upgrade.is_status_error)
