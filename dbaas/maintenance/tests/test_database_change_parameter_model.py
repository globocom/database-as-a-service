# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.test import TestCase
from ..models import DatabaseChangeParameter
from .factory import DatabaseChangeParameterFactory


class DatabaseChangeParameterTestCase(TestCase):

    def setUp(self):
        self.database_change_parameter = DatabaseChangeParameterFactory()

    def tearDown(self):
        self.database_change_parameter.delete()

    def test_update_step(self):
        self.assertIsNone(self.database_change_parameter.started_at)
        self.assertEqual(
            self.database_change_parameter.status,
            DatabaseChangeParameter.WAITING
        )
        self.assertEqual(self.database_change_parameter.current_step, 0)

        self.database_change_parameter.update_step(1)
        self.assertIsNotNone(self.database_change_parameter.started_at)
        self.assertEqual(
            self.database_change_parameter.status,
            DatabaseChangeParameter.RUNNING
        )
        self.assertEqual(self.database_change_parameter.current_step, 1)

        started_at_first = self.database_change_parameter.started_at
        self.database_change_parameter.update_step(2)
        self.assertEqual(
            self.database_change_parameter.started_at, started_at_first
        )
        self.assertEqual(
            self.database_change_parameter.status,
            DatabaseChangeParameter.RUNNING
        )
        self.assertEqual(self.database_change_parameter.current_step, 2)

    def test_status_error(self):
        self.assertIsNone(self.database_change_parameter.finished_at)
        self.assertEqual(
            self.database_change_parameter.status,
            DatabaseChangeParameter.WAITING
        )

        self.database_change_parameter.set_error()
        self.assertIsNotNone(self.database_change_parameter.finished_at)
        self.assertEqual(
            self.database_change_parameter.status,
            DatabaseChangeParameter.ERROR
        )

    def test_status_success(self):
        self.assertIsNone(self.database_change_parameter.finished_at)
        self.assertEqual(
            self.database_change_parameter.status,
            DatabaseChangeParameter.WAITING
        )

        self.database_change_parameter.set_success()
        self.assertIsNotNone(self.database_change_parameter.finished_at)
        self.assertEqual(
            self.database_change_parameter.status,
            DatabaseChangeParameter.SUCCESS
        )

    def test_is_status_error(self):
        self.assertFalse(self.database_change_parameter.is_status_error)

        self.database_change_parameter.set_error()
        self.assertTrue(self.database_change_parameter.is_status_error)

    def test_is_status_running(self):
        self.assertFalse(self.database_change_parameter.is_running)

        self.database_change_parameter.update_step(1)
        self.assertTrue(self.database_change_parameter.is_running)

    def test_can_do_retry(self):
        self.assertTrue(self.database_change_parameter.can_do_retry)

    def test_can_do_retry_to_other_database(self):
        self.assertTrue(self.database_change_parameter.can_do_retry)

        new_change_parameter = DatabaseChangeParameterFactory()
        self.assertTrue(new_change_parameter.can_do_retry)

        self.assertTrue(self.database_change_parameter.can_do_retry)

    def test_cannot_do_retry(self):
        self.assertTrue(self.database_change_parameter.can_do_retry)

        new_change_parameter = DatabaseChangeParameterFactory(
            database=self.database_change_parameter.database
        )
        self.assertTrue(new_change_parameter.can_do_retry)

        old_change_parameter = DatabaseChangeParameter.objects.get(
            id=self.database_change_parameter.id
        )
        self.assertFalse(old_change_parameter.can_do_retry)
