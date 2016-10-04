# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.test import TestCase
from physical.errors import NoDiskOfferingError


class TaskHistoryTestCase(TestCase):

    def test_can_add_message_detail(self):
        size = 123
        message = 'No disk offering greater than {}kb'.format(size)
        no_disk_offering = NoDiskOfferingError(size)
        self.assertEqual(no_disk_offering.message, message)
