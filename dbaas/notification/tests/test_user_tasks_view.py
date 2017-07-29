# coding: utf-8
from datetime import datetime
from mock import patch, MagicMock, PropertyMock
from unittest import TestCase
from notification.models import save_task, TaskHistory
from notification.tests.factory import TaskHistoryFactory
from notification.views import UserTasks


@patch('notification.views.get_redis_connection')
class GetNotificationsTestCase(TestCase):
    def setUp(self):
        self.view = UserTasks()

    def test_keys_query(self, mock_conn):
        mock_conn = mock_conn()

        self.view.get_notifications('fake_user')

        self.assertTrue(mock_conn.keys.called)
        self.assertEqual(mock_conn.keys.call_args[0][0], 'task_users:fake_user:*')

    def test_hgetall(self, mock_conn):
        mock_conn = mock_conn()
        mock_conn.keys.return_value = [
            'user_tasks:fake_user:1',
            'user_tasks:fake_user:2',
            'user_tasks:fake_user:3'
        ]
        self.view.get_notifications('fake_user')

        self.assertEqual(mock_conn.hgetall.call_count, 3)

    @patch('__builtin__.sorted')
    def test_sorted(self, mock_sorted, mock_conn):
        mock_conn = mock_conn()

        self.view.get_notifications('fake_user')

        self.assertTrue(mock_sorted.called)


@patch('notification.views.get_redis_connection')
class PostTestCase(TestCase):
    def setUp(self):
        fake_body = PropertyMock(return_value='''{
            "ids": [
                {"id": "1", "status": "RUNNING"},
                {"id": "2", "status": "WAITING"},
                {"id": "3", "status": "SUCCESS"}
            ]
        }''')
        UserTasks.request = PropertyMock(
            return_value=type('FakeRequest', (object,), {'body': fake_body})
        )

        self.view = UserTasks()

    def test_hget(self, mock_conn):
        mock_conn = mock_conn()

        self.view.post(**{'username': 'fake_user'})

        self.assertEqual(mock_conn.hget.call_count, 3)
        call_list = mock_conn.hget.call_args_list
        self.assertEqual(call_list[0][0][0], 'task_users:fake_user:1')
        self.assertEqual(call_list[1][0][0], 'task_users:fake_user:2')
        self.assertEqual(call_list[2][0][0], 'task_users:fake_user:3')

    def _fake_hget_result(self, *args, **kw):
        if args[0][-1] == '1':
            return 'RUNNING'
        elif args[0][-1] == '2':
            return 'ERROR'
        elif args[0][-1] == '3':
            return 'SUCCESS'

    def test_is_new_0_when_status_equal(self, mock_conn):
        mock_conn = mock_conn()
        mock_conn.hget.side_effect = self._fake_hget_result

        self.view.post(**{'username': 'fake_user'})

        call_list = mock_conn.hset.call_args_list
        self.assertEqual(mock_conn.hset.call_count, 2)
        self.assertEqual(call_list[0][0][0], 'task_users:fake_user:1')
        self.assertEqual(call_list[1][0][0], 'task_users:fake_user:3')


class GetTestCase(TestCase):
    def setUp(self):
        self.view = UserTasks()
        self.view.get_notifications = MagicMock(return_value=[])

    def test_get_notification_called(self):
        self.view.get()

        self.assertTrue(self.view.get_notifications.called)
