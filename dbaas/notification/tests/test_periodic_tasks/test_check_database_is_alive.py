from django.test import TestCase
from mock import patch, MagicMock

from model_mommy import mommy

from dbaas.tests.helpers import DatabaseHelper
from logical.models import Database
from notification.tasks import check_database_is_alive


@patch('logical.models.Database.update_status', new=MagicMock())
@patch('notification.tasks.get_worker_name', new=MagicMock())
@patch('notification.tasks.TaskHistory.register')
class DatabaseStatusTestCase(TestCase):

    def setUp(self):
        self.task_history = mommy.make(
            'TaskHistory',
            task_name='notification.tasks.database_status',
        )

    def test_database_alive(self, task_register_mock):
        database = DatabaseHelper.create(name='test', status=Database.ALIVE)
        task_register_mock.return_value = self.task_history
        check_database_is_alive(database)

        self.assertEqual(self.task_history.task_status, 'SUCCESS')
        self.assertIn('Database test is Alive', self.task_history.details)

    def test_database_initializing(self, task_register_mock):
        database = DatabaseHelper.create(
            name='test', status=Database.INITIALIZING
        )
        task_register_mock.return_value = self.task_history
        check_database_is_alive(database)

        self.assertEqual(self.task_history.task_status, 'SUCCESS')
        self.assertIn('Database test is Initializing',
                      self.task_history.details
                      )

    def test_database_alert(self, task_register_mock):
        database = DatabaseHelper.create(name='test', status=Database.ALERT)
        task_register_mock.return_value = self.task_history
        check_database_is_alive(database)

        self.assertEqual(self.task_history.task_status, 'ERROR')
        self.assertIn('Database test is Alert', self.task_history.details)

    def test_database_dead(self, task_register_mock):
        database = DatabaseHelper.create(name='test', status=Database.DEAD)
        task_register_mock.return_value = self.task_history
        check_database_is_alive(database)

        self.assertEqual(self.task_history.task_status, 'ERROR')
        self.assertIn('Database test is Dead', self.task_history.details)
