# -*- coding: utf-8 -*-
from __future__ import absolute_import

from mock import patch, MagicMock
from django.test import TestCase

from logical.tests.factory import DatabaseFactory
from notification.tasks import update_infra_instances_sizes
from physical.models import Instance
from contextlib import contextmanager


@contextmanager
class FakeClient(object):

    def info(self):
        return {
            'used_memory': 40
        }


@patch('notification.tasks.get_worker_name', new=MagicMock())
@patch('notification.tasks.TaskHistory')
@patch('logical.models.Database.driver')
class UpdateInfraInstancesSizesTestCase(TestCase):

    def setUp(self):
        self.database = DatabaseFactory.create(
            databaseinfra__engine__engine_type__name='redis'
        )

    def tearDown(self):
        Instance.objects.all().delete()

    def test_updated_for_one_database(self, mock_driver, mock_task_history):
        mock_driver.update_infra_instances_used_size.return_value = []
        mock_task_history.STATUS_SUCCESS = 'SUCCESS'
        update_infra_instances_sizes()

        self.assertEqual(mock_driver.update_infra_instances_sizes.call_count, 1)
        update_status_for = mock_task_history.register().update_status_for
        self.assertTrue(update_status_for.called)
        self.assertEqual(update_status_for.call_args[0][0], 'SUCCESS')

    def test_updated_for_one_database_with_error(self, mock_driver, mock_task_history):
        mock_driver.update_infra_instances_sizes.side_effect = TypeError
        mock_task_history.STATUS_ERROR = 'ERROR'
        update_infra_instances_sizes()

        self.assertEqual(mock_driver.update_infra_instances_sizes.call_count, 1)
        update_status_for = mock_task_history.register().update_status_for
        self.assertTrue(update_status_for.called)
        self.assertEqual(update_status_for.call_args[0][0], 'ERROR')
