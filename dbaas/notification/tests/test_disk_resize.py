# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.test import TestCase
from dbaas_nfsaas.models import HostAttr
from physical.tests import factory as physical_factory
from logical.tests import factory as logical_factory
from ..tasks_disk_resize import update_used_kb
from .factory import NotificationHistoryFactory

UPDATE_USED_SIZE_SUCCESS = '---> Used disk size updated. NFS: {}'
UPDATE_USED_SIZE_WRONG_HOST = '---> {} not found for: {}'
UPDATE_USED_SIZE_WITHOUT_NFSAAS = \
    '---> Could not update disk size used: Instance {} do not have NFSaaS disk'


class DiskResizeTestCase(TestCase):

    def setUp(self):
        self.task = NotificationHistoryFactory()
        self.instance = physical_factory.InstanceFactory()
        self.databaseinfra = self.instance.databaseinfra

        self.database = logical_factory.DatabaseFactory()
        self.database.databaseinfra = self.databaseinfra
        self.database.save()

    def test_can_update_used_kb(self):
        nfsaas_host = physical_factory.NFSaaSHostAttr()
        nfsaas_host.host = self.instance.hostname
        nfsaas_host.save()

        old_used_size = nfsaas_host.nfsaas_used_size_kb

        self.assertIsNone(self.task.details)
        is_updated = update_used_kb(
            database=self.database, task=self.task,
            address=self.instance.address, used_size=300
        )
        self.assertTrue(is_updated)

        expected_message = UPDATE_USED_SIZE_SUCCESS.format(
            nfsaas_host.nfsaas_path_host
        )
        self.assertEqual(expected_message, self.task.details)

        nfsaas_host = HostAttr.objects.get(pk=nfsaas_host.pk)
        self.assertNotEqual(nfsaas_host.nfsaas_used_size_kb, old_used_size)
        self.assertEqual(nfsaas_host.nfsaas_used_size_kb, 300)

    def test_cannot_update_used_kb_without_nfsaas(self):
        is_updated = update_used_kb(
            database=self.database, task=self.task,
            address=self.instance.address, used_size=300
        )
        self.assertFalse(is_updated)

        expected_message = UPDATE_USED_SIZE_WITHOUT_NFSAAS.format(
            self.instance.address
        )
        self.assertEqual(expected_message, self.task.details)

    def test_cannot_update_used_kb_wrong_host(self):
        is_updated = update_used_kb(
            database=self.database, task=self.task,
            address=self.instance.address[::-1], used_size=300
        )
        self.assertFalse(is_updated)

        expected_message = UPDATE_USED_SIZE_WRONG_HOST.format(
            self.instance.address[::-1], self.database.name
        )
        self.assertEqual(expected_message, self.task.details)
