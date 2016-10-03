# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.test import TestCase
from .factory import NotificationHistoryFactory


class TaskHistoryTestCase(TestCase):

    def setUp(self):
        self.task = NotificationHistoryFactory()

    def test_can_add_message_detail(self):
        self.assertIsNone(self.task.details)

        self.task.add_detail(message='Testing')
        self.assertEqual('Testing', self.task.details)

        self.task.add_detail(message='Again, with new line')
        self.assertEqual('Testing\nAgain, with new line', self.task.details)
