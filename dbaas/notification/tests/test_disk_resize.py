# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.test import TestCase
from physical.models import Volume
from physical.tests import factory as physical_factory
from logical.tests import factory as logical_factory
from ..tasks_disk_resize import update_disk
from .factory import TaskHistoryFactory

UPDATE_USED_SIZE_SUCCESS = '---> Used disk size updated. NFS: {}'
UPDATE_USED_SIZE_WRONG_HOST = '---> {} not found for: {}'
UPDATE_USED_SIZE_WITHOUT_VOLUME = \
    '---> Could not update disk size used: Instance {} do not have disk'


class DiskResizeTestCase(TestCase):

    def setUp(self):
        self.task = TaskHistoryFactory()
        self.instance = physical_factory.InstanceFactory()
        self.databaseinfra = self.instance.databaseinfra

        self.database = logical_factory.DatabaseFactory()
        self.database.databaseinfra = self.databaseinfra
        self.database.save()

    def test_can_update_disk_kb(self):
        volume = physical_factory.VolumeFactory()
        volume.host = self.instance.hostname
        volume.save()

        old_size = volume.total_size_kb
        old_used_size = volume.used_size_kb

        self.assertIsNone(self.task.details)
        is_updated = update_disk(
            database=self.database, task=self.task,
            address=self.instance.address, used_size=400, total_size=1000
        )
        self.assertTrue(is_updated)

        expected_message = UPDATE_USED_SIZE_SUCCESS.format(volume.identifier)
        self.assertEqual(expected_message, self.task.details)

        volume = Volume.objects.get(pk=volume.pk)
        self.assertNotEqual(volume.total_size_kb, old_size)
        self.assertNotEqual(volume.used_size_kb, old_used_size)
        self.assertEqual(volume.total_size_kb, 1000)
        self.assertEqual(volume.used_size_kb, 400)

    def test_cannot_update_disk_kb_without_volume(self):
        is_updated = update_disk(
            database=self.database, task=self.task,
            address=self.instance.address, used_size=300, total_size=100
        )
        self.assertFalse(is_updated)

        expected_message = UPDATE_USED_SIZE_WITHOUT_VOLUME.format(
            self.instance.address
        )
        self.assertEqual(expected_message, self.task.details)

    def test_cannot_update_disk_kb_wrong_host(self):
        is_updated = update_disk(
            database=self.database, task=self.task,
            address=self.instance.address[::-1], used_size=300, total_size=100
        )
        self.assertFalse(is_updated)

        expected_message = UPDATE_USED_SIZE_WRONG_HOST.format(
            self.instance.address[::-1], self.database.name
        )
        self.assertEqual(expected_message, self.task.details)
