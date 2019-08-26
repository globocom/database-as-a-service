from django.contrib import admin
from django.core.cache import cache
from django.test import TestCase
from system.models import Configuration
from admin.snapshot import SnapshotAdmin
from models import Snapshot


class MakeDatabaseBackup(TestCase):

    def setUp(self):
        cache.clear()

        self.admin = SnapshotAdmin(Snapshot, admin.sites.AdminSite())
        self.param_backup_available = Configuration(
            name='backup_available', value=1
        )
        self.param_backup_available.save()

    def tearDown(self):
        if self.param_backup_available.id:
            self.param_backup_available.delete()

    def test_is_backup_available(self):
        self.assertTrue(self.admin.is_backup_available)

    def test_is_backup_disable(self):
        self.param_backup_available.value = 0
        self.param_backup_available.save()
        self.assertFalse(self.admin.is_backup_available)

    def test_is_backup_disable_not_configured(self):
        self.param_backup_available.delete()
        self.assertFalse(self.admin.is_backup_available)
