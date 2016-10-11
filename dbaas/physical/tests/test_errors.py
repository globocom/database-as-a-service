# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.test import TestCase
from system.models import Configuration
from physical.errors import NoDiskOfferingError, NoDiskOfferingLesserError, \
    NoDiskOfferingGreaterError, DiskOfferingMaxAutoResize


class PhysicalErrorsTestCase(TestCase):

    def setUp(self):
        self.auto_resize_max_size_in_gb = Configuration(
            name='auto_resize_max_size_in_gb', value=100
        )
        self.auto_resize_max_size_in_gb.save()

    def tearDown(self):
        self.auto_resize_max_size_in_gb.delete()

    def test_no_disk_offering(self):
        size = 123
        typo = 'testing'
        message = 'No disk offering {} than {}kb'.format(typo, size)
        no_disk_offering = NoDiskOfferingError(typo=typo, size=size)
        self.assertEqual(no_disk_offering.message, message)

    def test_no_disk_offering_lesser(self):
        size = 456
        message = 'No disk offering lesser than {}kb'.format(size)
        no_disk_offering = NoDiskOfferingLesserError(size=size)
        self.assertEqual(no_disk_offering.message, message)

    def test_no_disk_offering_greater(self):
        size = 789
        message = 'No disk offering greater than {}kb'.format(size)
        no_disk_offering = NoDiskOfferingGreaterError(size=size)
        self.assertEqual(no_disk_offering.message, message)

    def test_disk_auto_resize_max_value(self):
        message = 'Disk auto resize can not be greater than {}GB'.format(
            self.auto_resize_max_size_in_gb.value
        )
        no_disk_offering = DiskOfferingMaxAutoResize()
        self.assertEqual(no_disk_offering.message, message)
