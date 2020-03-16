from mock import patch

from workflow.steps.util.volume_provider import TakeSnapshotFromMaster
from . import SingleInstanceBaseTestCase, HABaseTestCase

__all__ = ('SMMSingleInstanceTestCase', 'SMMHATestCase')


class SMMSingleInstanceTestCase(SingleInstanceBaseTestCase):
    step_class = TakeSnapshotFromMaster

    @patch('physical.models.DatabaseInfra.get_driver')
    @patch('backup.tasks.make_instance_snapshot_backup')
    @patch('backup.tasks.BackupGroup')
    def test_volume_attr(self, backup_group_mock, make_snapshot_mock,
                         get_driver_mock):
        get_driver_mock().get_master_instance.return_value = (
            self.master_instance
        )
        make_snapshot_mock.return_value = self.snapshot
        backup_group_mock.return_value = self.backup_group
        self.step.do()
        self.assertEqual(
            make_snapshot_mock.call_args[1]['target_volume'],
            self.master_volume
        )


class SMMHATestCase(HABaseTestCase):
    step_class = TakeSnapshotFromMaster

    @patch('physical.models.DatabaseInfra.get_driver')
    @patch('backup.tasks.make_instance_snapshot_backup')
    @patch('backup.tasks.BackupGroup')
    def test_volume_attr(self, backup_group_mock, make_snapshot_mock,
                         get_driver_mock):
        get_driver_mock().get_master_instance.return_value = (
            self.master_instance
        )
        make_snapshot_mock.return_value = self.snapshot
        backup_group_mock.return_value = self.backup_group
        self.step.do()
        self.assertEqual(
            make_snapshot_mock.call_args[1]['target_volume'],
            self.master_volume
        )
