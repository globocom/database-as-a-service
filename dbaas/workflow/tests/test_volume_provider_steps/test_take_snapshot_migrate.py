from mock import patch, MagicMock

from workflow.steps.util.volume_provider import (
    VolumeProviderSnapshotHasWarningStatusError,
    VolumeProviderSnapshotNotFoundError
)
from backup.models import Snapshot
from .base import SingleInstanceBaseTestCase, HABaseTestCase


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
