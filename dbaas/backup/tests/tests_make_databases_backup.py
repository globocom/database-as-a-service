from unittest import TestCase
from mock import patch, MagicMock, Mock
from datetime import datetime

from django.db.models import signals
from model_mommy import mommy

from backup.tasks import make_databases_backup
from backup.models import Snapshot, BackupGroup
from logical.models import Database


class TestMakeDatabasesBackup(TestCase):

    def setUp(self):
        self.backup_hour = 5
        self.year = 2020
        self.month = 1
        self.day = 1

        signals.post_save.disconnect(sender=Database, dispatch_uid="database_drive_credentials")

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
        self.infra = mommy.make(
            'DatabaseInfra', backup_hour=self.backup_hour,
            plan__has_persistence=True,
            environment=self.dev_env
        )
        self.instance = mommy.make(
            'Instance', databaseinfra=self.infra
        )
        self.database = mommy.make(
            'Database', databaseinfra=self.infra, environment=self.dev_env
        )

    @patch('backup.tasks.make_instance_snapshot_backup')
    @patch('backup.models.BackupGroup.save')
    @patch('backup.tasks.get_now')
    @patch('notification.models.TaskHistory.register')
    @patch('backup.tasks.get_worker_name')
    def test_only_backup_current_hour(
        self, get_worker_name_mock, task_register, datetime_now,
        save_backup_group, make_instance_snapshot_backup
    ):
        get_worker_name_mock.return_value = 'test'
        datetime_now.return_value = datetime(
                year=self.year, month=self.month, day=self.day,
                hour=self.backup_hour
        )
        group = BackupGroup()
        save_backup_group.return_value = group
        make_instance_snapshot_backup.return_value.status.return_value = Snapshot.SUCCESS
        make_databases_backup()
        make_instance_snapshot_backup.assert_called_with(
            instance=self.instance, error={}, group=group
        )
