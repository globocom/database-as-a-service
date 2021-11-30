# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from django.core.cache import cache
from django.test import TestCase
from django.contrib import admin
from physical.tests.factory import DiskOfferingFactory, EnvironmentFactory
from physical.errors import NoDiskOfferingGreaterError, NoDiskOfferingLesserError
from system.models import Configuration
from ..admin.disk_offering import DiskOfferingAdmin
from ..forms.disk_offerring import DiskOfferingForm
from ..models import DiskOffering

LOG = logging.getLogger(__name__)
SEARCH_FIELDS = ('name', )
LIST_FIELDS = ('name', 'size_gb', 'selected_environments')
SAVE_ON_TOP = True
UNICODE_FORMAT = '{}'


class DiskOfferingTestCase(TestCase):

    def create_basic_disks(self):
        for disk_offering in DiskOffering.objects.all():
            for plan in disk_offering.plans.all():
                plan.databaseinfras.all().delete()
            disk_offering.plans.all().delete()
            disk_offering.delete()
        cache.clear()

        self.bigger = DiskOfferingFactory()
        self.bigger.size_kb *= 30
        self.bigger.environments.add(self.environment)
        self.bigger.save()

        self.medium = DiskOfferingFactory()
        self.medium.size_kb *= 20
        self.medium.environments.add(self.environment)
        self.medium.save()

        self.smaller = DiskOfferingFactory()
        self.smaller.size_kb *= 10
        self.smaller.environments.add(self.environment)
        self.smaller.save()

    def setUp(self):
        self.admin = DiskOfferingAdmin(DiskOffering, admin.sites.AdminSite())
        self.auto_resize_max_size_in_gb = Configuration(
            name='auto_resize_max_size_in_gb', value=100
        )
        self.auto_resize_max_size_in_gb.save()
        self.environment = EnvironmentFactory()

    def tearDown(self):
        if self.auto_resize_max_size_in_gb.id:
            self.auto_resize_max_size_in_gb.delete()

    def test_search_fields(self):
        self.assertEqual(SEARCH_FIELDS, self.admin.search_fields)

    def test_list_fields(self):
        self.assertEqual(LIST_FIELDS, self.admin.list_display)

    def test_save_position(self):
        self.assertEqual(SAVE_ON_TOP, self.admin.save_on_top)

    def test_adding_gb_to_kb(self):
        disk_offering_form = DiskOfferingForm(
            data={
                'name': 'disk_offering_small',
                'size_gb': 0.5,
                'environments': [self.environment.id]
            }
        )
        self.assertTrue(disk_offering_form.is_valid())
        self.admin.save_model(
            request=None, obj=disk_offering_form.instance,
            form=disk_offering_form, change=None
        )

        disk_offering = DiskOffering.objects.get(name='disk_offering_small')
        self.assertEqual(disk_offering.size_gb(), 0.5)
        self.assertEqual(disk_offering.size_kb, 524288)

    def test_editing_gb_to_kb(self):
        disk_factory = DiskOfferingFactory()
        disk_offering = DiskOffering.objects.get(pk=disk_factory.pk)
        self.assertEqual(disk_offering.size_gb(), 1)
        self.assertEqual(disk_offering.size_kb, 1048576)

        disk_offering_form = DiskOfferingForm(
            data={
                'name': disk_offering.name,
                'size_gb': 1.5,
                'environments': [self.environment.id]
            },
            instance=disk_offering
        )
        self.assertTrue(disk_offering_form.is_valid())
        self.admin.save_model(
            request=None, obj=disk_offering,
            form=disk_offering_form, change=None
        )
        self.assertEqual(disk_offering.size_gb(), 1.5)
        self.assertEqual(disk_offering.size_kb, 1572864)

    def test_edit_initial_values(self):
        disk_offering_form = DiskOfferingForm()
        self.assertNotIn('name', disk_offering_form.initial)
        self.assertIn('size_gb', disk_offering_form.initial)
        self.assertIsNone(disk_offering_form.initial['size_gb'])

        disk_factory = DiskOfferingFactory()
        disk_offering = DiskOffering.objects.get(pk=disk_factory.pk)

        disk_offering_form = DiskOfferingForm(instance=disk_offering)
        self.assertEqual(
            disk_offering_form.initial['name'], disk_offering.name
        )
        self.assertEqual(
            disk_offering_form.initial['size_gb'], disk_offering.size_gb()
        )

    def test_model_sizes(self):
        disk_factory = DiskOfferingFactory()
        self.assertEqual(disk_factory.size_kb, 1048576)
        self.assertEqual(disk_factory.size_gb(), 1.0)
        self.assertEqual(disk_factory.size_bytes(), 1073741824)

        disk_offering = DiskOffering()
        self.assertIsNone(disk_offering.size_kb)
        self.assertIsNone(disk_offering.size_gb())
        self.assertIsNone(disk_offering.size_bytes())

    def test_model_converter(self):
        disk_factory = DiskOfferingFactory()
        self.assertEqual(disk_factory.converter_kb_to_gb(1572864), 1.5)
        self.assertEqual(disk_factory.converter_kb_to_bytes(524288), 536870912)
        self.assertEqual(disk_factory.converter_gb_to_kb(0.75), 786432)

        self.assertIsNone(disk_factory.converter_kb_to_gb(0))
        self.assertIsNone(disk_factory.converter_kb_to_bytes(0))
        self.assertIsNone(disk_factory.converter_gb_to_kb(0))

    def test_unicode(self):
        disk_offering = DiskOffering()
        expected_unicode = UNICODE_FORMAT.format(disk_offering.name)
        self.assertEqual(expected_unicode, str(disk_offering))

    def test_disk_offering_is_in_admin(self):
        self.assertIn(DiskOffering, admin.site._registry)
        admin_class = admin.site._registry[DiskOffering]
        self.assertIsInstance(admin_class, DiskOfferingAdmin)

    def test_can_found_greater_disk(self):
        self.create_basic_disks()

        found = DiskOffering.first_greater_than(
            self.smaller.size_kb, self.environment)
        self.assertEqual(self.medium, found)

        found = DiskOffering.first_greater_than(
            self.medium.size_kb, self.environment)
        self.assertEqual(self.bigger, found)

    def test_cannot_found_greater_disk(self):
        self.create_basic_disks()

        self.assertRaises(
            NoDiskOfferingGreaterError,
            DiskOffering.first_greater_than, self.bigger.size_kb, self.environment
        )

    def test_can_found_greater_disk_with_exclude(self):
        self.create_basic_disks()

        found = DiskOffering.first_greater_than(
            self.smaller.size_kb, self.environment, exclude_id=self.medium.id
        )
        self.assertEqual(self.bigger, found)

    def test_can_found_disk_for_auto_resize(self):
        self.create_basic_disks()

        self.auto_resize_max_size_in_gb.value = int(self.bigger.size_gb())
        self.auto_resize_max_size_in_gb.save()
        found = DiskOffering.last_offering_available_for_auto_resize(
            self.environment)
        self.assertEqual(self.bigger, found)

        self.auto_resize_max_size_in_gb.value = int(self.bigger.size_gb()) - 1
        self.auto_resize_max_size_in_gb.save()
        found = DiskOffering.last_offering_available_for_auto_resize(
            self.environment)
        self.assertEqual(self.medium, found)

    def test_cannot_found_disk_for_auto_resize(self):
        self.create_basic_disks()

        self.auto_resize_max_size_in_gb.value = int(self.smaller.size_gb()) - 1
        self.auto_resize_max_size_in_gb.save()
        self.assertRaises(
            NoDiskOfferingLesserError,
            DiskOffering.last_offering_available_for_auto_resize, self.environment
        )

    def test_compare_disks(self):
        self.create_basic_disks()

        self.assertGreater(self.bigger, self.smaller)
        self.assertLess(self.smaller, self.bigger)

        self.medium_twice = DiskOfferingFactory()
        self.medium_twice.size_kb *= 20
        self.medium_twice.save()

        self.assertEqual(self.medium, self.medium)
        self.assertNotEqual(self.medium, self.medium_twice)

        self.medium_twice.delete()

    def test_disk_is_last_offering(self):
        self.create_basic_disks()
        self.auto_resize_max_size_in_gb.value = int(self.medium.size_gb()) + 1
        self.auto_resize_max_size_in_gb.save()

        self.assertFalse(
            self.smaller.is_last_auto_resize_offering(self.environment)
        )
        self.assertTrue(
            self.medium.is_last_auto_resize_offering(self.environment)
        )
        self.assertFalse(
            self.bigger.is_last_auto_resize_offering(self.environment)
        )

    def test_disk_is_last_offering_without_param(self):
        self.create_basic_disks()
        self.auto_resize_max_size_in_gb.delete()

        self.assertFalse(
            self.smaller.is_last_auto_resize_offering(self.environment)
        )
        self.assertFalse(
            self.medium.is_last_auto_resize_offering(self.environment)
        )
        self.assertTrue(
            self.bigger.is_last_auto_resize_offering(self.environment)
        )
