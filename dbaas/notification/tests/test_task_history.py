# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.test import TestCase
from notification.models import TaskHistory
from notification.tests.factory import TaskHistoryFactory
from logical.tests.factory import DatabaseFactory
from logical.models import Database


class TaskHistoryObjectTestCase(TestCase):
    @classmethod
    def setUpClass(self):
        self.database = DatabaseFactory()
        self.task = TaskHistoryFactory(
            object_class=self.database._meta.object_name,
            object_id=self.database.id,
            task_status=TaskHistory.STATUS_WAITING
        )

    @classmethod
    def tearDownClass(self):
        Database.objects.all().delete()
        TaskHistory.objects.all().delete()

    def test_return_true_when_have_task_history_registered(self):

        self.assertTrue(self.database.is_being_used_elsewhere())

    def test_return_false_when_have_task_history_registered_in_another_database(self):
        other_database = DatabaseFactory()
        self.assertFalse(other_database.is_being_used_elsewhere())


class TaskHistoryTestCase(TestCase):

    def setUp(self):
        self.task = TaskHistoryFactory()

    def test_can_add_message_detail(self):
        self.assertIsNone(self.task.details)

        self.task.add_detail(message='Testing')
        self.assertEqual('Testing', self.task.details)

        self.task.add_detail(message='Again, with new line')
        self.assertEqual('Testing\nAgain, with new line', self.task.details)

    def test_can_add_message_detail_with_level(self):
        self.assertIsNone(self.task.details)

        self.task.add_detail(message='Testing', level=1)
        self.assertEqual('-> Testing', self.task.details)

        self.task.add_detail(message='Again, with new line', level=2)
        self.assertEqual('-> Testing\n--> Again, with new line', self.task.details)

    def test_can_add_step(self):
        self.assertIsNone(self.task.details)

        step = 1
        total = 15
        description = 'testing'
        message = '- Step {} of {} - {}'.format(step, total, description)
        self.task.add_step(step=step, total=total, description=description)
        self.assertIn(message, self.task.details)

    def test_can_get_running_tasks(self):
        self.task.task_status = TaskHistory.STATUS_RUNNING
        self.task.save()

        tasks = TaskHistory.running_tasks()
        self.assertIsNotNone(tasks)
        self.assertIn(self.task, tasks)

    def test_can_get_running_tasks_empty(self):
        tasks = TaskHistory.running_tasks()
        self.assertEqual(len(tasks), 0)

    def test_can_get_waiting_tasks(self):
        self.task.task_status = TaskHistory.STATUS_WAITING
        self.task.save()

        tasks = TaskHistory.waiting_tasks()
        self.assertIsNotNone(tasks)
        self.assertIn(self.task, tasks)

    def test_can_get_waiting_tasks_empty(self):
        tasks = TaskHistory.waiting_tasks()
        self.assertEqual(len(tasks), 0)

    def test_is_running(self):
        self.task.task_status = TaskHistory.STATUS_RUNNING
        self.assertTrue(self.task.is_running)

    def test_is_not_running(self):
        self.task.task_status = TaskHistory.STATUS_SUCCESS
        self.assertFalse(self.task.is_running)

    def test_is_error(self):
        self.task.task_status = TaskHistory.STATUS_ERROR
        self.assertTrue(self.task.is_status_error)

    def test_is_not_error(self):
        self.task.task_status = TaskHistory.STATUS_SUCCESS
        self.assertFalse(self.task.is_status_error)
