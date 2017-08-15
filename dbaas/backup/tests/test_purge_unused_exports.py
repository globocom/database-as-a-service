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

    def tearDown(self):
        HostAttr.objects.all().delete()

    @patch('backup.tasks.delete_export')
    def test_delete_only_inactive(self, delete_export_method):
        export = NFSaaSHostAttr()
        export.host = self.instance.hostname
        export.is_active = False
        export.save()

        export_active = NFSaaSHostAttr()
        export_active.host = self.instance.hostname
        export_active.save()

        exports = HostAttr.objects.all()
        self.assertEqual(2, len(exports))
        self.assertIn(export, exports)
        self.assertIn(export_active, exports)

        self.assertTrue(purge_unused_exports())

        exports = HostAttr.objects.all()
        self.assertEqual(1, len(exports))
        self.assertNotIn(export, exports)
        self.assertIn(export_active, exports)

        delete_export_method.assert_called()
        delete_export_method.assert_called_once_with(
            self.environment, export.nfsaas_path_host
        )

    def test_cannot_delete_inactive_with_active_snapshot(self):
        export = NFSaaSHostAttr()
        export.host = self.instance.hostname
        export.is_active = False
        export.save()

        snapshot = SnapshotFactory(instance=self.instance)
        snapshot.export_path = export.nfsaas_path
        snapshot.save()

        snapshot = SnapshotFactory(instance=self.instance)
        snapshot.export_path = export.nfsaas_path
        snapshot.purge_at = datetime.now()
        snapshot.save()

        exports = HostAttr.objects.all()
        self.assertEqual(1, len(exports))
        self.assertIn(export, exports)

        self.assertTrue(purge_unused_exports())

        exports = HostAttr.objects.all()
        self.assertEqual(1, len(exports))
        self.assertIn(export, exports)

    @patch('backup.tasks.delete_export')
    def test_can_delete_inactive_with_inactive_snapshot(
        self, delete_export_method
    ):
        export = NFSaaSHostAttr()
        export.host = self.instance.hostname
        export.is_active = False
        export.save()

        snapshot = SnapshotFactory(instance=self.instance)
        snapshot.export_path = export.nfsaas_path
        snapshot.purge_at = datetime.now()
        snapshot.save()

        exports = HostAttr.objects.all()
        self.assertEqual(1, len(exports))
        self.assertIn(export, exports)

        self.assertTrue(purge_unused_exports())

        exports = HostAttr.objects.all()
        self.assertEqual(0, len(exports))
        self.assertNotIn(export, exports)

        delete_export_method.assert_called()
        delete_export_method.assert_called_once_with(
            self.environment, export.nfsaas_path_host
        )

    @patch('backup.tasks.delete_export')
    def test_task_with_success(self, delete_export_method):
        export = NFSaaSHostAttr()
        export.host = self.instance.hostname
        export.is_active = False
        export.save()

        exports = HostAttr.objects.all()
        self.assertEqual(1, len(exports))
        self.assertIn(export, exports)

        task = TaskHistoryFactory()
        self.assertIsNone(task.details)

        self.assertTrue(purge_unused_exports(task))

        exports = HostAttr.objects.all()
        self.assertEqual(0, len(exports))
        self.assertNotIn(export, exports)

        self.assertIn('Removing: {}'.format(export), task.details)
        self.assertIn('Success', task.details)

        delete_export_method.assert_called()
        delete_export_method.assert_called_once_with(
            self.environment, export.nfsaas_path_host
        )

    @patch('backup.tasks.delete_export')
    def test_task_with_error(self, delete_export_method):
        delete_export_method.side_effect = Exception('Fake error')

        export = NFSaaSHostAttr()
        export.host = self.instance.hostname
        export.is_active = False
        export.save()

        exports = HostAttr.objects.all()
        self.assertEqual(1, len(exports))
        self.assertIn(export, exports)

        task = TaskHistoryFactory()
        self.assertIsNone(task.details)

        self.assertFalse(purge_unused_exports(task))

        exports = HostAttr.objects.all()
        self.assertEqual(1, len(exports))
        self.assertIn(export, exports)

        self.assertIn('Removing: {}'.format(export), task.details)
        self.assertIn('Error: Fake error'.format(export), task.details)

        delete_export_method.assert_called()
        delete_export_method.assert_called_once_with(
            self.environment, export.nfsaas_path_host
        )
