from django.test import TestCase
from mock import patch, call, Mock
from datetime import datetime

from model_mommy import mommy

from backup.tasks import make_databases_backup
from backup.models import Snapshot, BackupGroup
from dbaas.tests.helpers import DatabaseHelper, InfraHelper, PlanHelper


def assert_not_called_with(self, *args, **kwargs):
    try:
        self.assert_called_with(*args, **kwargs)
    except AssertionError:
        return
    raise AssertionError(
        'Expected %s to not have been called.' %
        self._format_mock_call_signature(args, kwargs)
    )


Mock.assert_not_called_with = assert_not_called_with

FAKE_NOW = datetime(2020, 1, 1, 5, 10, 00)


class FakeDatetime(datetime):
    @staticmethod
    def now():
        return FAKE_NOW


class TestMakeDatabasesBackup(TestCase):

    def setUp(self):
        self.backup_hour = 5
        self.year = 2020
        self.month = 1
        self.day = 1

        mommy.make(
            'Configuration', name='backup_hour', value=str(self.backup_hour)
        )
        mommy.make(
            'Configuration', name='prod_envs', value='prod,prod-cm,aws-prod'
        )
        mommy.make(
            'Configuration', name='dev_envs', value='dev,qa2,aws-dev'
        )
        self.dev_env = mommy.make('Environment', name='dev')
        mommy.make('Environment', name='prod')
        _, _, _, self.plan = PlanHelper.create()
        self.infra = InfraHelper.create(
            backup_hour=self.backup_hour,
            plan__has_persistence=True,
            environment=self.dev_env,
            plan=self.plan
        )
        self.instance = mommy.make(
            'Instance', databaseinfra=self.infra
        )
        self.database = DatabaseHelper.create(
            databaseinfra=self.infra,
            environment=self.dev_env
        )

    @patch('backup.tasks.make_instance_snapshot_backup')
    @patch('backup.models.BackupGroup.save')
    @patch('backup.tasks.datetime', FakeDatetime)
    @patch('notification.models.TaskHistory.register')
    @patch('backup.tasks.get_worker_name')
    def test_backup_current_hour(
        self, get_worker_name_mock, task_register, save_backup_group,
        make_instance_snapshot_backup
    ):
        get_worker_name_mock.return_value = 'test'
        group = BackupGroup()
        save_backup_group.return_value = group
        make_instance_snapshot_backup.return_value.status.return_value = (
            Snapshot.SUCCESS
        )

        make_databases_backup()
        make_instance_snapshot_backup.assert_called_with(
            current_hour=self.backup_hour, instance=self.instance, error={},
            group=group
        )

    @patch('backup.tasks.make_instance_snapshot_backup')
    @patch('backup.models.BackupGroup.save')
    @patch('backup.tasks.datetime', FakeDatetime)
    @patch('notification.models.TaskHistory.register')
    @patch('backup.tasks.get_worker_name')
    def test_current_hour_without_pending_backup(
        self, get_worker_name_mock, task_register, save_backup_group,
        make_instance_snapshot_backup
    ):
        infra_mock = InfraHelper.create(
            name='pending_backup_test',
            backup_hour=self.backup_hour-1,
            plan__has_persistence=True,
            environment=self.dev_env,
            plan=self.plan
        )
        DatabaseHelper.create(
            databaseinfra=infra_mock,
            environment=self.dev_env
        )

        instance_mock = mommy.make(
            'Instance', databaseinfra=infra_mock
        )

        get_worker_name_mock.return_value = 'test'
        group = BackupGroup()
        save_backup_group.return_value = group
        snapshot_mock = mommy.make(
            'Snapshot', instance=instance_mock, group=group)
        snapshot_mock.status = Snapshot.SUCCESS
        make_instance_snapshot_backup.return_value = snapshot_mock

        make_databases_backup()
        calls = [
            call(
                current_hour=self.backup_hour, instance=self.instance,
                error={}, group=group
            ),
            call(
                current_hour=self.backup_hour, instance=instance_mock,
                error={}, group=group
            )
        ]
        make_instance_snapshot_backup.assert_has_calls(calls, any_order=True)

    @patch('backup.tasks.make_instance_snapshot_backup')
    @patch('backup.models.BackupGroup.save')
    @patch('backup.tasks.datetime', FakeDatetime)
    @patch('notification.models.TaskHistory.register')
    @patch('backup.tasks.get_worker_name')
    def test_current_hour_with_pending_backup(
        self, get_worker_name_mock, task_register, save_backup_group,
        make_instance_snapshot_backup
    ):
        infra_mock = InfraHelper.create(
            name='pending_backup_test',
            backup_hour=self.backup_hour-1,
            plan__has_persistence=True,
            environment=self.dev_env,
            plan=self.plan
        )
        DatabaseHelper.create(
            databaseinfra=infra_mock, environment=self.dev_env
        )

        instance_mock = mommy.make(
            'Instance', databaseinfra=infra_mock
        )

        get_worker_name_mock.return_value = 'test'
        group = BackupGroup()
        save_backup_group.return_value = group
        make_instance_snapshot_backup.return_value.status.return_value = (
            Snapshot.SUCCESS
        )

        make_databases_backup()
        calls = [
            call(
                current_hour=self.backup_hour, instance=self.instance,
                error={}, group=group
            ),
            call(
                current_hour=self.backup_hour, instance=instance_mock,
                error={}, group=group
            )
        ]
        make_instance_snapshot_backup.assert_has_calls(calls, any_order=True)
