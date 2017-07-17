from mock import patch
from physical.tests.factory import HostFactory, EnvironmentFactory
from ..util.disk import CreateExport, MigrationCreateExport, AddDiskPermissionsOldest
from . import TestBaseStep


class DiskStepTests(TestBaseStep):

    def setUp(self):
        super(DiskStepTests, self).setUp()
        self.host = self.instance.hostname

    def test_environment(self):
        migration = CreateExport(self.instance)
        self.assertEqual(migration.environment, self.environment)

    def test_host(self):
        migration = CreateExport(self.instance)
        self.assertEqual(migration.host, self.host)


class DiskStepTestsMigration(TestBaseStep):

    def setUp(self):
        super(DiskStepTestsMigration, self).setUp()
        self.host = self.instance.hostname
        self.future_host = HostFactory()
        self.host.future_host = self.future_host
        self.host.save()

        self.environment_migrate = EnvironmentFactory()
        self.environment.migrate_environment = self.environment_migrate
        self.environment.save()

    def test_environment_migration(self):
        migration = MigrationCreateExport(self.instance)
        self.assertEqual(migration.environment, self.environment_migrate)

    def test_host_migration(self):
        migration = MigrationCreateExport(self.instance)
        self.assertEqual(migration.host, self.future_host)

    @patch('workflow.steps.util.disk.AddDiskPermissionsOldest.get_disk_path')
    @patch('workflow.steps.util.disk.create_access')
    def test_add_permission_oldest(self, create_access, get_disk_path):
        get_disk_path.return_value = self.future_host.hostname

        add_permission = AddDiskPermissionsOldest(self.instance)
        add_permission.do()

        create_access.assert_called()
        create_access.assert_called_once_with(
            self.environment, self.future_host.hostname, self.host.future_host
        )
