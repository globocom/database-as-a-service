# coding: utf-8
from mock import patch
from unittest import TestCase
from rest_framework import status
from rest_framework.response import Response

from maintenance.models import DatabaseCreate, DatabaseMaintenanceTask
from logical.models import Database
from tsuru.views import check_database_status
from notification.tests.factory import TaskHistoryFactory


@patch('tsuru.views.get_database')
@patch('tsuru.views.last_database_create')
class CheckDatabaseStatusTestCase(TestCase):

    def setUp(self):
        self.fake_database_create = DatabaseCreate()
        self.fake_database_create.task = TaskHistoryFactory.build()
        self.fake_database = Database()

    def test_check_database_status_success(self, mock_database_create, mock_database):
        self.fake_database_create.status = DatabaseMaintenanceTask.SUCCESS
        mock_database_create.return_value = self.fake_database_create
        mock_database.return_value = self.fake_database

        response = check_database_status('test_database', 'dev')
        self.assertIsInstance(response, Database)

    def test_check_database_status_running(self, mock_database_create, mock_database):
        self.fake_database_create.status = DatabaseMaintenanceTask.RUNNING
        mock_database_create.return_value = self.fake_database_create
        mock_database.return_value = self.fake_database

        response = check_database_status('test_database', 'dev')
        self.assertIsInstance(response, Response)
        self.assertEqual(response.status_code, status.HTTP_412_PRECONDITION_FAILED)

    def test_check_database_status_error(self, mock_database_create, mock_database):
        self.fake_database_create.status = DatabaseMaintenanceTask.ERROR
        mock_database_create.return_value = self.fake_database_create
        mock_database.return_value = self.fake_database

        response = check_database_status('test_database', 'dev')
        self.assertIsInstance(response, Response)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
