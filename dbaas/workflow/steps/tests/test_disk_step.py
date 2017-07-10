from physical.tests.factory import HostFactory, EnvironmentFactory
from ..util.disk import CreateExport, MigrationCreateExport
from . import TestBaseStep


class DiskStepTests(TestBaseStep):

    def setUp(self):
        super(DiskStepTests, self).setUp()
        self.host = self.instance.hostname

    def test_environment(self):
        migration = CreateExport(self.instance)
        self.assertEqual(migration.environment, self.environment)

    def test_hos(self):
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
