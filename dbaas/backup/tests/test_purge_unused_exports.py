from datetime import datetime
from unittest import TestCase
from mock import patch
from dbaas_nfsaas.models import HostAttr
from notification.tests.factory import TaskHistoryFactory
from physical.tests.factory import InstanceFactory, NFSaaSHostAttr
from ..tasks import purge_unused_exports
from factory import SnapshotFactory


class PurgeUnusedExports(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.instance = InstanceFactory(port=1000)
        cls.environment = cls.instance.databaseinfra.environment

    def setUp(self):
        self.export = NFSaaSHostAttr()
        self.export.host = self.instance.hostname
        self.export.is_active = False
        self.export.save()

        self.assertEqual(1, len(self.exports))
        self.assertIn(self.export, self.exports)

    @property
    def exports(self):
        return HostAttr.objects.all()

    def tearDown(self):
        HostAttr.objects.all().delete()

    @patch('backup.tasks.delete_export')
    def test_delete_only_inactive(self, delete_export_method):
        export_active = NFSaaSHostAttr()
        export_active.host = self.instance.hostname
        export_active.save()

        self.assertEqual(2, len(self.exports))
        self.assertIn(self.export, self.exports)
        self.assertIn(export_active, self.exports)

        self.assertTrue(purge_unused_exports())

        self.assertEqual(1, len(self.exports))
        self.assertNotIn(self.export, self.exports)
        self.assertIn(export_active, self.exports)

        delete_export_method.assert_called()
        delete_export_method.assert_called_once_with(
            self.environment, self.export.nfsaas_path_host
        )

    def test_cannot_delete_inactive_with_active_snapshot(self):
        snapshot = SnapshotFactory(instance=self.instance)
        snapshot.export_path = self.export.nfsaas_path
        snapshot.save()

        snapshot = SnapshotFactory(instance=self.instance)
        snapshot.export_path = self.export.nfsaas_path
        snapshot.purge_at = datetime.now()
        snapshot.save()

        self.assertTrue(purge_unused_exports())

        self.assertEqual(1, len(self.exports))
        self.assertIn(self.export, self.exports)

    @patch('backup.tasks.delete_export')
    def test_can_delete_inactive_with_inactive_snapshot(
        self, delete_export_method
    ):
        snapshot = SnapshotFactory(instance=self.instance)
        snapshot.export_path = self.export.nfsaas_path
        snapshot.purge_at = datetime.now()
        snapshot.save()

        self.assertEqual(1, len(self.exports))
        self.assertIn(self.export, self.exports)

        self.assertTrue(purge_unused_exports())

        self.assertEqual(0, len(self.exports))
        self.assertNotIn(self.export, self.exports)

        delete_export_method.assert_called()
        delete_export_method.assert_called_once_with(
            self.environment, self.export.nfsaas_path_host
        )

    @patch('backup.tasks.delete_export')
    def test_task_with_success(self, delete_export_method):

        task = TaskHistoryFactory()
        self.assertIsNone(task.details)

        self.assertTrue(purge_unused_exports(task))

        self.assertEqual(0, len(self.exports))
        self.assertNotIn(self.export, self.exports)

        self.assertIn('Removing: {}'.format(self.export), task.details)
        self.assertIn('Success', task.details)

        delete_export_method.assert_called()
        delete_export_method.assert_called_once_with(
            self.environment, self.export.nfsaas_path_host
        )

    @patch('backup.tasks.delete_export')
    def test_task_with_error(self, delete_export_method):
        delete_export_method.side_effect = Exception('Fake error')

        task = TaskHistoryFactory()
        self.assertIsNone(task.details)

        self.assertFalse(purge_unused_exports(task))

        self.assertEqual(1, len(self.exports))
        self.assertIn(self.export, self.exports)

        self.assertIn('Removing: {}'.format(self.export), task.details)
        self.assertIn('Error: Fake error'.format(self.export), task.details)

        delete_export_method.assert_called()
        delete_export_method.assert_called_once_with(
            self.environment, self.export.nfsaas_path_host
        )
