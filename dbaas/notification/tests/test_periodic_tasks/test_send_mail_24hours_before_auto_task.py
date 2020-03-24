from django.test import TestCase
from mock import patch, MagicMock
from datetime import datetime, timedelta
from itertools import cycle

from model_mommy import mommy
from model_mommy.recipe import seq

from physical.models import Instance
from dbaas.tests.helpers import InstanceHelper
from notification.tasks import send_mail_24hours_before_auto_task
from maintenance.models import TaskSchedule
from dbaas.tests.helpers import DatabaseHelper, InfraHelper, PlanHelper


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

    # @patch('notification.tasks.maintenance_models.TaskSchedule.objects.filter')
    # def test_dont_find_infras(self, filter_mock):
    #     self.databaseinfra.ssl_configured = False
    #     self.databaseinfra.save()
    #     check_ssl_expire_at()
    #     self.assertFalse(filter_mock.called)
    #
    # @patch('notification.tasks.Configuration.get_by_name',
    #        new=MagicMock(return_value='other_env'))
    # @patch('notification.tasks.maintenance_models.TaskSchedule.objects.filter')
    # def test_dont_find_infras_if_env_configured(self, filter_mock):
    #     check_ssl_expire_at()
    #     self.assertFalse(filter_mock.called)
    #
    # @patch('notification.tasks.maintenance_models.TaskSchedule.objects.create')
    # @patch('maintenance.models.schedule_task_notification', new=MagicMock())
    # def test_already_have_task_scheduled(self, create_mock):
    #     task_schedule = TaskSchedule()
    #     task_schedule.database = self.database
    #     task_schedule.scheduled_for = self.one_month_later
    #     task_schedule.status = TaskSchedule.SCHEDULED
    #     task_schedule.save()
    #     check_ssl_expire_at()
    #     self.assertFalse(create_mock.called)
    #
    # def test_create_task_scheduled(self):
    #     task_schedule = TaskSchedule.objects.filter(database=self.database)
    #     self.hostname.ssl_expire_at = self.one_month_later
    #     self.hostname.save()
    #     self.assertEqual(task_schedule.count(), 0)
    #     check_ssl_expire_at()
    #     task_schedule = TaskSchedule.objects.filter(database=self.database)
    #     self.assertEqual(task_schedule.count(), 1)
    #
    # def test_create_task_scheduled_percona(self):
    #     self.engine_type.name = 'mysql_percona'
    #     self.engine_type.save()
    #     task_schedule = TaskSchedule.objects.filter(database=self.database)
    #     self.hostname.ssl_expire_at = self.one_month_later
    #     self.hostname.save()
    #     self.assertEqual(task_schedule.count(), 0)
    #     check_ssl_expire_at()
    #     task_schedule = TaskSchedule.objects.filter(database=self.database)
    #     self.assertEqual(task_schedule.count(), 1)
    #
    # @patch('notification.tasks.Configuration.get_by_name',
    #        new=MagicMock(return_value='fake_env'))
    # def test_create_task_scheduled_if_configured(self):
    #     task_schedule = TaskSchedule.objects.filter(database=self.database)
    #     self.hostname.ssl_expire_at = self.one_month_later
    #     self.hostname.save()
    #     self.assertEqual(task_schedule.count(), 0)
    #     check_ssl_expire_at()
    #     task_schedule = TaskSchedule.objects.filter(database=self.database)
    #     self.assertEqual(task_schedule.count(), 1)
    #
    # def _fake_get_by_name(self, conf_name):
    #     if conf_name == 'schedule_send_mail':
    #         return 0
    #     else:
    #         return self.check_ssl_envs
    #
    # @patch('notification.tasks.Configuration.get_by_name')
    # def test_create_task_scheduled_if_configured_multiple_envs(
    #         self, get_by_name_mock):
    #     self.check_ssl_envs = 'fake_env,another_env'
    #     get_by_name_mock.side_effect = self._fake_get_by_name
    #     environment, databaseinfra, hostname, database = self._create_database(
    #         env_name='another_env',
    #         infra_name='__test__ another_infra'
    #     )
    #     task_schedule = TaskSchedule.objects.filter(database=self.database)
    #     self.hostname.ssl_expire_at = self.one_month_later
    #     self.hostname.save()
    #     hostname.ssl_expire_at = self.one_month_later
    #     hostname.save()
    #     self.assertEqual(task_schedule.count(), 0)
    #     check_ssl_expire_at()
    #     task_schedule = TaskSchedule.objects.all()
    #     self.assertEqual(task_schedule.count(), 2)
    #
    # @patch('notification.tasks.date')
    # def test_create_task_scheduled_next_maintenance_window(self, date_mock):
    #     date_mock.today.return_value = FAKE_TODAY
    #     self.databaseinfra.maintenance_window = 3
    #     self.databaseinfra.maintenance_day = 5
    #     self.databaseinfra.save()
    #     check_ssl_expire_at()
    #     task_schedule = TaskSchedule.objects.get(database=self.database)
    #     self.assertEqual(
    #         task_schedule.scheduled_for.weekday(),
    #         4
    #     )
    #     self.assertEqual(
    #         task_schedule.scheduled_for.date().strftime("%Y-%m-%d"),
    #         "2019-12-27"
    #     )
    #     self.assertEqual(task_schedule.scheduled_for.hour, 3)
