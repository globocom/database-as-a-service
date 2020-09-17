from django.test import TestCase
from mock import patch, MagicMock
from datetime import date, timedelta

from model_mommy import mommy

from physical.models import Instance
from dbaas.tests.helpers import InstanceHelper
from notification.tasks import check_ssl_expire_at
from maintenance.models import TaskSchedule
from dbaas.tests.helpers import DatabaseHelper, InfraHelper, PlanHelper


__all__ = ('CheckSslExpireAt',)
FAKE_TODAY = date(2019, 12, 17)


class FakeDate(date):
    @staticmethod
    def today():
        return FAKE_TODAY


@patch('notification.tasks.get_worker_name', new=MagicMock())
@patch('notification.tasks.TaskHistory', new=MagicMock())
class CheckSslExpireAt(TestCase):
    instance_helper = InstanceHelper

    def setUp(self):
        self.today = FAKE_TODAY
        self.engine_type, self.engine, _, self.plan = PlanHelper.create()
        self.environment, self.databaseinfra, self.hostname, self.database = (
            self._create_database()
        )
        self.one_month_later = self.today + timedelta(days=30)

    def _create_database(self, env_name='fake_env',
                         infra_name='__test__ mysqlinfra2'):
        environment = mommy.make(
            'Environment',
            name=env_name
        )
        databaseinfra = InfraHelper.create(
            name=infra_name,
            user="root", password='fake_pass',
            engine=self.engine,
            plan=self.plan,
            ssl_configured=True,
            environment=environment
        )
        hostname = mommy.make(
            'Host',
            ssl_expire_at=FAKE_TODAY + timedelta(days=16)
        )
        self.instance_helper.create_instances_by_quant(
            instance_type=Instance.MYSQL, qt=1,
            infra=databaseinfra, hostname=hostname
        )
        database = DatabaseHelper.create(
            name='test_db_1',
            databaseinfra=databaseinfra,
        )
        return environment, databaseinfra, hostname, database

    @patch('notification.tasks.maintenance_models.TaskSchedule.objects.filter')
    def test_dont_find_infras(self, filter_mock):
        self.databaseinfra.ssl_configured = False
        self.databaseinfra.save()
        check_ssl_expire_at()
        self.assertFalse(filter_mock.called)

    @patch('notification.tasks.maintenance_models.TaskSchedule.objects.create')
    @patch('maintenance.models.schedule_task_notification', new=MagicMock())
    def test_already_have_task_scheduled(self, create_mock):
        task_schedule = TaskSchedule()
        task_schedule.database = self.database
        task_schedule.scheduled_for = self.one_month_later
        task_schedule.status = TaskSchedule.SCHEDULED
        task_schedule.save()
        check_ssl_expire_at()
        self.assertFalse(create_mock.called)

    def test_create_task_scheduled(self):
        task_schedule = TaskSchedule.objects.filter(database=self.database)
        self.hostname.ssl_expire_at = self.one_month_later
        self.hostname.save()
        self.assertEqual(task_schedule.count(), 0)
        check_ssl_expire_at()
        task_schedule = TaskSchedule.objects.filter(database=self.database)
        self.assertEqual(task_schedule.count(), 1)

    def test_create_task_scheduled_percona(self):
        self.engine_type.name = 'mysql_percona'
        self.engine_type.save()
        task_schedule = TaskSchedule.objects.filter(database=self.database)
        self.hostname.ssl_expire_at = self.one_month_later
        self.hostname.save()
        self.assertEqual(task_schedule.count(), 0)
        check_ssl_expire_at()
        task_schedule = TaskSchedule.objects.filter(database=self.database)
        self.assertEqual(task_schedule.count(), 1)

    @patch('notification.tasks.Configuration.get_by_name',
           new=MagicMock(return_value='fake_env'))
    def test_create_task_scheduled_if_configured(self):
        task_schedule = TaskSchedule.objects.filter(database=self.database)
        self.hostname.ssl_expire_at = self.one_month_later
        self.hostname.save()
        self.assertEqual(task_schedule.count(), 0)
        check_ssl_expire_at()
        task_schedule = TaskSchedule.objects.filter(database=self.database)
        self.assertEqual(task_schedule.count(), 1)

    def _fake_get_by_name(self, conf_name):
        if conf_name == 'schedule_send_mail':
            return 0
        else:
            return self.check_ssl_envs

    @patch('notification.tasks.Configuration.get_by_name')
    def test_create_task_scheduled_if_configured_multiple_envs(
            self, get_by_name_mock):
        self.check_ssl_envs = 'fake_env,another_env'
        get_by_name_mock.side_effect = self._fake_get_by_name
        environment, databaseinfra, hostname, database = self._create_database(
            env_name='another_env',
            infra_name='__test__ another_infra'
        )
        task_schedule = TaskSchedule.objects.filter(database=self.database)
        self.hostname.ssl_expire_at = self.one_month_later
        self.hostname.save()
        hostname.ssl_expire_at = self.one_month_later
        hostname.save()
        self.assertEqual(task_schedule.count(), 0)
        check_ssl_expire_at()
        task_schedule = TaskSchedule.objects.all()
        self.assertEqual(task_schedule.count(), 2)

    @patch('notification.tasks.date')
    def test_create_task_scheduled_next_maintenance_window(self, date_mock):
        date_mock.today.return_value = FAKE_TODAY
        self.databaseinfra.maintenance_window = 3
        self.databaseinfra.maintenance_day = 5
        self.databaseinfra.save()
        check_ssl_expire_at()
        task_schedule = TaskSchedule.objects.get(database=self.database)
        self.assertEqual(
            task_schedule.scheduled_for.weekday(),
            4
        )
        self.assertEqual(
            task_schedule.scheduled_for.date().strftime("%Y-%m-%d"),
            "2019-12-27"
        )
        self.assertEqual(task_schedule.scheduled_for.hour, 3)
