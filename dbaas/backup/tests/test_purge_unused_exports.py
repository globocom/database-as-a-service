from datetime import datetime
from unittest import TestCase
from mock import patch
from notification.tests.factory import TaskHistoryFactory
from physical.tests.factory import InstanceFactory, VolumeFactory
from physical.models import Volume
from backup.tasks import purge_unused_exports
from factory import SnapshotFactory


class PurgeUnusedExports(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.instance = InstanceFactory(port=1000)
        cls.environment = cls.instance.databaseinfra.environment

    def setUp(self):
        self.export = VolumeFactory()
        self.export.host = self.instance.hostname
        self.export.is_active = False
        self.export.save()

        self.assertEqual(1, len(self.exports))
        self.assertIn(self.export, self.exports)

    @property
    def exports(self):
        return Volume.objects.all()

    def tearDown(self):
        Volume.objects.all().delete()

    @patch('backup.tasks.VolumeProviderBase.destroy_volume')
    @patch('backup.tasks.VolumeProviderBase.clean_up')
    @patch('backup.tasks.VolumeProviderBase.add_access')
    def test_delete_only_inactive(self, add_access, clean_up, destroy):
        self.assertTrue(purge_unused_exports())

        add_access.assert_called_once_with(self.export, self.export.host)
        clean_up.assert_called_once_with(self.export)
        destroy.assert_called_once_with(self.export)

    @patch('backup.tasks.VolumeProviderBase.destroy_volume')
    @patch('backup.tasks.VolumeProviderBase.clean_up')
    @patch('backup.tasks.VolumeProviderBase.add_access')
    def test_cannot_delete_inactive_with_active_snapshot(
        self, add_access, clean_up, destroy
    ):
        snapshot = SnapshotFactory(instance=self.instance)
        snapshot.volume = self.export
        snapshot.save()

        snapshot = SnapshotFactory(instance=self.instance)
        snapshot.volume = self.export
        snapshot.purge_at = datetime.now()
        snapshot.save()

        self.assertTrue(purge_unused_exports())

        add_access.assert_not_called()
        clean_up.assert_not_called()
        destroy.assert_not_called()

    @patch('backup.tasks.VolumeProviderBase.destroy_volume')
    @patch('backup.tasks.VolumeProviderBase.clean_up')
    @patch('backup.tasks.VolumeProviderBase.add_access')
    def test_can_delete_inactive_with_inactive_snapshot(
        self, add_access, clean_up, destroy
    ):
        snapshot = SnapshotFactory(instance=self.instance)
        snapshot.volume = self.export
        snapshot.purge_at = datetime.now()
        snapshot.save()

        self.assertTrue(purge_unused_exports())

        add_access.assert_called_once_with(self.export, self.export.host)
        clean_up.assert_called_once_with(self.export)
        destroy.assert_called_once_with(self.export)

    @patch('backup.tasks.VolumeProviderBase.destroy_volume', new=None)
    @patch('backup.tasks.VolumeProviderBase.clean_up', new=None)
    @patch('backup.tasks.VolumeProviderBase.add_access', new=None)
    def test_task_with_success(self):
        task = TaskHistoryFactory()
        self.assertIsNone(task.details)
        self.assertTrue(purge_unused_exports(task))
        self.assertIn('Removing: {}'.format(self.export), task.details)
        self.assertIn('Success', task.details)

    @patch('backup.tasks.VolumeProviderBase.add_access')
    def test_task_with_error(self, add_access):
        add_access.side_effect = Exception('Fake error')

        task = TaskHistoryFactory()
        self.assertIsNone(task.details)
        self.assertFalse(purge_unused_exports(task))
        self.assertIn('Removing: {}'.format(self.export), task.details)
        self.assertIn('Error: Fake error'.format(self.export), task.details)
