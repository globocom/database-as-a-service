from django.test import TestCase
from mock import patch, MagicMock
from datetime import datetime, timedelta
from itertools import cycle

from model_mommy import mommy
from model_mommy.recipe import seq

from dbaas.tests.helpers import InstanceHelper
from notification.tasks import send_mail_24hours_before_auto_task
from dbaas.tests.helpers import DatabaseHelper


__all__ = ('SendMailTestCase',)
FAKE_NOW = datetime(2019, 12, 17, 12, 10, 00)


class FakeDatetime(datetime):
    @staticmethod
    def now():
        return FAKE_NOW


@patch('notification.tasks.get_worker_name', new=MagicMock())
@patch('notification.tasks.TaskHistory', new=MagicMock())
class SendMailTestCase(TestCase):
    instance_helper = InstanceHelper

    def setUp(self):
        self.now = FAKE_NOW
        self.one_hour_later = self.now + timedelta(hours=1)
        self.databases = DatabaseHelper.create(
            name=seq('fake_db_name'), _quantity=3
        )

    @patch('notification.tasks.post_save.send')
    @patch('notification.tasks.datetime', FakeDatetime)
    def test_dont_find_any_tasks(self, send_mock):
        mommy.make(
            'TaskSchedule',
            database=cycle(self.databases),
            scheduled_for=seq(FAKE_NOW, timedelta(hours=1)),
            status=0,
            _quantity=3
        )
        send_mock.reset_mock()
        send_mail_24hours_before_auto_task()
        self.assertFalse(send_mock.called)

    @patch('notification.tasks.post_save.send')
    @patch('notification.tasks.datetime', FakeDatetime)
    def test_find_one_task(self, send_mock):
        tasks = mommy.make(
            'TaskSchedule',
            database=cycle(self.databases),
            scheduled_for=seq(FAKE_NOW, timedelta(hours=24)),
            status=0,
            _quantity=3
        )
        send_mock.reset_mock()
        send_mail_24hours_before_auto_task()
        self.assertTrue(send_mock.called)
        self.assertEqual(send_mock.call_count, 1)
        call_kwargs = send_mock.call_args[1]
        self.assertEqual(
            call_kwargs['instance'].database,
            self.databases[0]
        )
        self.assertDictEqual(
            call_kwargs,
            {
                'instance': tasks[0],
                'created': False,
                'execution_warning': True
            }
        )

    @patch('notification.tasks.post_save.send')
    @patch('notification.tasks.datetime', FakeDatetime)
    def test_find_three_task(self, send_mock):
        tasks = mommy.make(
            'TaskSchedule',
            database=cycle(self.databases),
            scheduled_for=FAKE_NOW + timedelta(hours=24),
            status=0,
            _quantity=3
        )
        send_mock.reset_mock()
        send_mail_24hours_before_auto_task()
        self.assertTrue(send_mock.called)
        self.assertEqual(send_mock.call_count, 3)
        call_kwargs_list = send_mock.call_args_list
        self.assertEqual(
            call_kwargs_list[0][1]['instance'].database,
            self.databases[0]
        )
        self.assertDictEqual(
            call_kwargs_list[0][1],
            {
                'instance': tasks[0],
                'created': False,
                'execution_warning': True
            }
        )
        self.assertEqual(
            call_kwargs_list[1][1]['instance'].database,
            self.databases[1]
        )
        self.assertDictEqual(
            call_kwargs_list[1][1],
            {
                'instance': tasks[1],
                'created': False,
                'execution_warning': True
            }
        )
        self.assertEqual(
            call_kwargs_list[2][1]['instance'].database,
            self.databases[2]
        )
        self.assertDictEqual(
            call_kwargs_list[2][1],
            {
                'instance': tasks[2],
                'created': False,
                'execution_warning': True
            }
        )
