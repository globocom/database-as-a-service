# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.test import TestCase
from physical.errors import NoDiskOfferingError, NoDiskOfferingLesserError, NoDiskOfferingGreaterError


class PhysicalErrorsTestCase(TestCase):

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
