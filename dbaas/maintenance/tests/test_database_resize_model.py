# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.test import TestCase
from ..models import DatabaseResize
from .factory import DatabaseResizeFactory


class DatabaseResizeTestCase(TestCase):

    def setUp(self):
        self.database_resize = DatabaseResizeFactory()

    def tearDown(self):
        self.database_resize.delete()

    def test_update_step(self):
        self.assertIsNone(self.database_resize.started_at)
        self.assertEqual(self.database_resize.status, DatabaseResize.WAITING)
        self.assertEqual(self.database_resize.current_step, 0)

        self.database_resize.update_step(1)
        self.assertIsNotNone(self.database_resize.started_at)
        self.assertEqual(self.database_resize.status, DatabaseResize.RUNNING)
        self.assertEqual(self.database_resize.current_step, 1)

        started_at_first = self.database_resize.started_at
        self.database_resize.update_step(2)
        self.assertEqual(self.database_resize.started_at, started_at_first)
        self.assertEqual(self.database_resize.status, DatabaseResize.RUNNING)
        self.assertEqual(self.database_resize.current_step, 2)

    def test_status_error(self):
        self.assertIsNone(self.database_resize.finished_at)
        self.assertEqual(self.database_resize.status, DatabaseResize.WAITING)

        self.database_resize.set_error()
        self.assertIsNotNone(self.database_resize.finished_at)
        self.assertEqual(self.database_resize.status, DatabaseResize.ERROR)

    def test_status_success(self):
        self.assertIsNone(self.database_resize.finished_at)
        self.assertEqual(self.database_resize.status, DatabaseResize.WAITING)

        self.database_resize.set_success()
        self.assertIsNotNone(self.database_resize.finished_at)
        self.assertEqual(self.database_resize.status, DatabaseResize.SUCCESS)

    def test_is_status_error(self):
        self.assertFalse(self.database_resize.is_status_error)

        self.database_resize.set_error()
        self.assertTrue(self.database_resize.is_status_error)

    def test_can_do_retry(self):
        self.assertTrue(self.database_resize.can_do_retry)

    def test_can_do_retry_to_other_database(self):
        self.assertTrue(self.database_resize.can_do_retry)

        new_resize = DatabaseResizeFactory()
        self.assertTrue(new_resize.can_do_retry)

        self.assertTrue(self.database_resize.can_do_retry)

    def test_cannot_do_retry(self):
        self.assertTrue(self.database_resize.can_do_retry)

        new_resize = DatabaseResizeFactory(
            database=self.database_resize.database,
            source_offer=self.database_resize.source_offer
        )
        self.assertTrue(new_resize.can_do_retry)

        old_resize = DatabaseResize.objects.get(id=self.database_resize.id)
        self.assertFalse(old_resize.can_do_retry)