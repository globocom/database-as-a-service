from django.test import TestCase
from mock import patch, MagicMock

from model_mommy import mommy
from model_mommy.recipe import seq

from dbaas.tests.helpers import DatabaseHelper
from logical.models import Database
from notification.tasks import check_databases_status


@patch('notification.tasks.get_worker_name', new=MagicMock())
@patch('notification.tasks.TaskHistory.register')
class DatabaseStatusTestCase(TestCase):

    def setUp(self):
        self.task_history = mommy.make(
            'TaskHistory',
            task_name='notification.tasks.check_databases_status',
        )

    def test_database_alive(self, task_register_mock):
        DatabaseHelper.create(status=Database.ALIVE, _quantity=4)
        task_register_mock.return_value = self.task_history
        check_databases_status()

        self.assertEqual(self.task_history.task_status, 'SUCCESS')
        self.assertIn('All databases are alive.', self.task_history.details)

    def test_database_initializing(self, task_register_mock):
        DatabaseHelper.create(status=Database.INITIALIZING, _quantity=4)
        task_register_mock.return_value = self.task_history
        check_databases_status()

        self.assertEqual(self.task_history.task_status, 'SUCCESS')
        self.assertIn('All databases are alive.', self.task_history.details)

    def test_database_alert(self, task_register_mock):
        DatabaseHelper.create(
            name=seq('test'), status=Database.ALERT, _quantity=4
        )
        task_register_mock.return_value = self.task_history
        check_databases_status()

        self.assertEqual(self.task_history.task_status, 'ERROR')
        self.assertIn('Alert', self.task_history.details)
        self.assertIn('test1', self.task_history.details)
        self.assertIn('test2', self.task_history.details)
        self.assertIn('test3', self.task_history.details)
        self.assertIn('test4', self.task_history.details)

    def test_database_dead(self, task_register_mock):
        DatabaseHelper.create(
            name=seq('test'), status=Database.DEAD, _quantity=4
        )
        task_register_mock.return_value = self.task_history
        check_databases_status()

        self.assertEqual(self.task_history.task_status, 'ERROR')
        self.assertIn('Dead', self.task_history.details)
        self.assertIn('test1', self.task_history.details)
        self.assertIn('test2', self.task_history.details)
        self.assertIn('test3', self.task_history.details)
        self.assertIn('test4', self.task_history.details)

    def test_databases_with_different_status(self, task_register_mock):
        DatabaseHelper.create(status=Database.INITIALIZING)
        DatabaseHelper.create(status=Database.ALIVE)
        database_alert = DatabaseHelper.create(status=Database.ALERT)
        database_dead = DatabaseHelper.create(status=Database.DEAD)
        task_register_mock.return_value = self.task_history
        check_databases_status()

        self.assertEqual(self.task_history.task_status, 'ERROR')
        self.assertIn('Alert', self.task_history.details)
        self.assertIn('Dead', self.task_history.details)
        self.assertIn(database_dead.name, self.task_history.details)
        self.assertIn(database_alert.name, self.task_history.details)
