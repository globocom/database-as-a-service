# -*- coding: utf-8 -*-
from __future__ import absolute_import
from json import loads
from django.test import TestCase
from django.core.urlresolvers import reverse
from notification.models import TaskHistory
from notification.views import running_tasks_api, waiting_tasks_api
from notification.tests.factory import TaskHistoryFactory


class UrlTest(TestCase):

    def test_can_access_tasks_running(self):
        url = reverse(running_tasks_api)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        tasks = loads(response.content)
        self.assertEqual(len(tasks), 0)

    def test_find_tasks_running(self):
        task_running = TaskHistoryFactory()
        task_running.task_status = TaskHistory.STATUS_RUNNING
        task_running.save()
        task_pending = TaskHistoryFactory()

        url = reverse(running_tasks_api)
        response = self.client.get(url)
        tasks = loads(response.content)

        self.assertIn(str(task_running.id), tasks)
        self.assertEqual(tasks[str(task_running.id)], task_running.task_name)
        self.assertNotIn(str(task_pending.id), tasks)

    def test_can_access_tasks_waiting(self):
        url = reverse(waiting_tasks_api)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        tasks = loads(response.content)
        self.assertEqual(len(tasks), 0)

    def test_find_tasks_waiting(self):
        task_waiting = TaskHistoryFactory()
        task_waiting.task_status = TaskHistory.STATUS_WAITING
        task_waiting.save()
        task_pending = TaskHistoryFactory()

        url = reverse(waiting_tasks_api)
        response = self.client.get(url)
        tasks = loads(response.content)

        self.assertIn(str(task_waiting.id), tasks)
        self.assertEqual(tasks[str(task_waiting.id)], task_waiting.task_name)
        self.assertNotIn(str(task_pending.id), tasks)
