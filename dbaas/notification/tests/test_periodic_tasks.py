from django.test import TestCase
from mock import patch, MagicMock
from datetime import date, timedelta

from physical.tests import factory as factory_physical
from physical.models import Instance
from logical.tests import factory as factory_logical
from dbaas.tests.helpers import InstanceHelper
from notification.tasks import check_ssl_expire_at
from maintenance.models import TaskSchedule


@patch('notification.tasks.get_worker_name', new=MagicMock())
@patch('notification.tasks.TaskHistory', new=MagicMock())
class CheckSslExpireAt(TestCase):
    instance_helper = InstanceHelper

    def setUp(self):
        self.today = date.today()
        self.engine_type = factory_physical.EngineTypeFactory(
            name='mysql'
        )
        self.engine = factory_physical.EngineFactory(
            engine_type=self.engine_type
        )
        self.plan = factory_physical.PlanFactory(
            engine=self.engine
        )
        self.databaseinfra = factory_physical.DatabaseInfraFactory(
            name="__test__ mysqlinfra2",
            user="root", password='fake_pass',
            engine=self.engine,
            plan=self.plan,
            ssl_configured=True
        )
        self.hostname = factory_physical.HostFactory()
        self.instances = self.instance_helper.create_instances_by_quant(
            instance_type=Instance.MYSQL, qt=1,
            infra=self.databaseinfra, hostname=self.hostname
        )
        self.instance = self.instances[0]
        self.database = factory_logical.DatabaseFactory(
            name='test_db_1',
            databaseinfra=self.databaseinfra,
        )
        self.one_month_later = self.today + timedelta(days=30)

    @patch('notification.tasks.TaskSchedule.objects.filter')
    def test_dont_find_infras(self, filter_mock):
        self.databaseinfra.ssl_configured = False
        check_ssl_expire_at()
        self.assertFalse(filter_mock.called)

    @patch('notification.tasks.TaskSchedule.objects.create')
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

    def test_create_task_scheduled_next_maintenance_window(self):
        task_schedule = TaskSchedule.objects.filter(database=self.database)
        self.hostname.ssl_expire_at = self.one_month_later
        self.hostname.save()
        self.databaseinfra.maintenance_window = 3
        self.databaseinfra.maintenance_day = 3
        self.databaseinfra.save()
        check_ssl_expire_at()
        task_schedule = TaskSchedule.objects.get(database=self.database)
        self.assertEqual(
            task_schedule.scheduled_for.weekday(),
            self.databaseinfra.maintenance_day
        )
        self.assertTrue(
            task_schedule.scheduled_for.date() >= self.one_month_later
        )
        self.assertEqual(task_schedule.scheduled_for.hour, 3)
