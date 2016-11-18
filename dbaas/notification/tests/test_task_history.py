# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.test import TestCase
from notification.models import TaskHistory
from notification.tests.factory import TaskHistoryFactory


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

    def test_can_get_running_tasks(self):
        self.task.task_status = TaskHistory.STATUS_RUNNING
        self.task.save()

        tasks = TaskHistory.running_tasks()
        self.assertIsNotNone(tasks)
        self.assertIn(self.task, tasks)

    def test_can_get_running_tasks_empty(self):
        tasks = TaskHistory.running_tasks()
        self.assertEqual(len(tasks), 0)
