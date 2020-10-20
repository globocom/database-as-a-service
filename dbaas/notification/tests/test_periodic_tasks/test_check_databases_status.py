from django.test import TestCase
from mock import patch, MagicMock, call

from model_mommy import mommy

from dbaas.tests.helpers import DatabaseHelper
from logical.models import Database
from notification.tasks import check_databases_status


@patch('notification.tasks.get_worker_name', new=MagicMock())
@patch('notification.tasks.TaskHistory.register')
class CheckDatabasesStatusTestCase(TestCase):

    def setUp(self):
        self.task_history = mommy.make(
            'TaskHistory',
            task_name='notification.tasks.check_databases_status',
        )

    def test_database_alive(self, task_register_mock):
        DatabaseHelper.create(status=Database.ALIVE)
        task_register_mock.return_value = self.task_history
        check_databases_status()

        self.assertEqual(self.task_history.task_status, 'SUCCESS')
        self.assertIn('All databases were checked.', self.task_history.details)

    def test_database_initializing(self, task_register_mock):
        DatabaseHelper.create(status=Database.INITIALIZING)
        task_register_mock.return_value = self.task_history
        check_databases_status()

        self.assertEqual(self.task_history.task_status, 'SUCCESS')
        self.assertIn('All databases were checked.', self.task_history.details)

    @patch('notification.tasks.check_database_is_alive.delay')
    def test_database_alert(self, check_database_is_alive, task_register_mock):
        database = DatabaseHelper.create(status=Database.ALERT)
        task_register_mock.return_value = self.task_history
        check_databases_status()

        check_database_is_alive.assert_called_with(database)
        self.assertEqual(self.task_history.task_status, 'SUCCESS')
        self.assertIn('All databases were checked.', self.task_history.details)

    @patch('notification.tasks.check_database_is_alive.delay')
    def test_database_dead(self, check_database_is_alive, task_register_mock):
        database = DatabaseHelper.create(status=Database.DEAD)
        task_register_mock.return_value = self.task_history
        check_databases_status()

        check_database_is_alive.assert_called_with(database)
        self.assertEqual(self.task_history.task_status, 'SUCCESS')
        self.assertIn('All databases were checked.', self.task_history.details)

    @patch('notification.tasks.check_database_is_alive.delay')
    def test_databases_with_different_status(
        self, check_database_is_alive, task_register_mock
    ):
        DatabaseHelper.create(status=Database.INITIALIZING)
        DatabaseHelper.create(status=Database.ALIVE)
        database_alert = DatabaseHelper.create(status=Database.ALERT)
        database_dead = DatabaseHelper.create(status=Database.DEAD)
        task_register_mock.return_value = self.task_history

        calls = [call(database_dead), call(database_alert)]

        check_databases_status()

        check_database_is_alive.assert_has_calls(calls)
        self.assertEqual(self.task_history.task_status, 'SUCCESS')
        self.assertIn('All databases were checked.', self.task_history.details)
