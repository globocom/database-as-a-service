from django.test import TestCase
from model_mommy import mommy

from dbaas.tests.helpers import InstanceHelper
from workflow.steps.util.volume_provider import TakeSnapshotMigrate
from maintenance.models import HostMigrate
from backup.models import Snapshot
from dbaas.tests.helpers import DatabaseHelper


class SingleInstanceBaseTestCase(TestCase):
    instance_helper = InstanceHelper
    step_class = TakeSnapshotMigrate

    def setUp(self):
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
        self.infra = mommy.make('DatabaseInfra', plan__has_persistence=True)
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

        self.database_migrate = mommy.make(
            'DatabaseMigrate',
            database=DatabaseHelper.create()
        )
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
