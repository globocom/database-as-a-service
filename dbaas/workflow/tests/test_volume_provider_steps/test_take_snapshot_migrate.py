from django.test import TestCase
from model_mommy import mommy
from mock import patch, MagicMock
from django.db.models import signals

from dbaas.tests.helpers import InstanceHelper
from logical.models import Database
from workflow.steps.util.volume_provider import (
    TakeSnapshotMigrate, VolumeProviderSnapshotHasWarningStatusError,
    VolumeProviderSnapshotNotFoundError
)
from maintenance.models import HostMigrate
from backup.models import Snapshot


__all__ = ('SingleInstanceBaseTestCase', 'HABaseTestCase',
           'SMSingleInstanceTestCase', 'SMHATestCase')


class SingleInstanceBaseTestCase(TestCase):
    instance_helper = InstanceHelper
    step_class = TakeSnapshotMigrate

    def setUp(self):
        signals.post_save.disconnect(
            sender=Database, dispatch_uid="database_drive_credentials"
        )
        self.master_future_host = mommy.make(
            'Host',
            hostname='master_future_host'
        )
        self.master_host = mommy.make(
            'Host',
            future_host=self.master_future_host,
            hostname='master_host'
        )
        self.master_volume = mommy.make(
            'Volume',
            host=self.master_host,
            identifier=1
        )
        self.master_furute_volume = mommy.make(
            'Volume',
            host=self.master_future_host,
            identifier=2
        )
        self.infra = mommy.make('DatabaseInfra')
        self.master_instance = self.instance_helper.create_instances_by_quant(
            infra=self.infra,
            hostname=self.master_host
        )[0]
        self.step = self.step_class(self.master_instance)
        self.backup_group = mommy.make('BackupGroup')
        self.snapshot = mommy.make(
            Snapshot,
            status=Snapshot.SUCCESS
        )
        self.database_migrate = mommy.make('DatabaseMigrate')
        self.host_migrate = mommy.make(
            HostMigrate,
            database_migrate=self.database_migrate,
            host=self.master_host,
            status=HostMigrate.RUNNING
        )


class HABaseTestCase(SingleInstanceBaseTestCase):
    def setUp(self):
        super(HABaseTestCase, self).setUp()
        self.master_host.future_host = None
        self.master_host.save()
        self.master_future_host.delete()
        self.master_furute_volume.delete()
        self.slave_future_host = mommy.make(
            'Host',
            hostname='slave_future_host'
        )
        self.slave_host = mommy.make(
            'Host',
            future_host=self.slave_future_host,
            hostname='slave_host'
        )
        self.slave_volume = mommy.make(
            'Volume',
            host=self.slave_host,
            identifier=3
        )
        self.slave_furute_volume = mommy.make(
            'Volume',
            host=self.slave_future_host,
            identifier=4
        )
        self.slave_instance = self.instance_helper.create_instances_by_quant(
            infra=self.infra,
            hostname=self.slave_host,
            base_address='199'
        )[0]
        self.host_migrate.host = self.slave_host
        self.host_migrate.save()
        self.step = self.step_class(self.slave_instance)
        self.step.step_manager = self.host_migrate


class SMSingleInstanceTestCase(SingleInstanceBaseTestCase):

    @patch('backup.tasks.make_instance_snapshot_backup')
    def test_dont_make_snapshot_again_if_has_snapshot_on_step_manager(
            self, make_backup_mock):
        self.host_migrate.snapshot = self.snapshot
        self.host_migrate.save()
        self.step.do()

        self.assertFalse(make_backup_mock.called)

    @patch('backup.tasks.make_instance_snapshot_backup',
           new=MagicMock())
    def test_volume_attr(self):
        provider = self.step.provider_class(self.master_instance)
        self.assertEqual(
            provider.volume,
            self.master_volume
        )

    @patch('backup.tasks.make_instance_snapshot_backup')
    def test_set_is_automatic_false_on_snapshot(self, make_backup_mock):
        self.snapshot.is_automatic = True
        self.snapshot.save()
        make_backup_mock.return_value = self.snapshot
        self.step.do()
        snapshot = Snapshot.objects.get(id=self.snapshot.id)

        self.assertFalse(snapshot.is_automatic)

    @patch('backup.tasks.make_instance_snapshot_backup')
    def test_raise_exception_when_dont_have_snapshot(
            self, make_backup_mock):
        make_backup_mock.return_value = None

        with self.assertRaises(VolumeProviderSnapshotNotFoundError):
            self.step.do()

    @patch('backup.tasks.make_instance_snapshot_backup')
    def test_raise_exception_when_snapshot_has_warning_status(
            self, make_backup_mock):
        self.snapshot.status = Snapshot.WARNING
        self.snapshot.save()
        make_backup_mock.return_value = self.snapshot

        with self.assertRaises(VolumeProviderSnapshotHasWarningStatusError):
            self.step.do()


class SMHATestCase(HABaseTestCase, SMSingleInstanceTestCase):

    @patch('backup.tasks.make_instance_snapshot_backup',
           new=MagicMock())
    def test_volume_attr(self):
        provider = self.step.provider_class(self.slave_instance)
        self.assertEqual(
            provider.volume,
            self.slave_volume
        )
