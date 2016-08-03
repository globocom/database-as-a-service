# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from django.test import TestCase
from django.contrib import admin
from django.core.cache import cache
from ..admin.disk_offering import DiskOfferingAdmin
from ..forms.disk_offerring import DiskOfferingForm
from ..models import DiskOffering
from physical.tests.factory import DiskOfferingFactory

LOG = logging.getLogger(__name__)
SEARCH_FIELDS = ('name', )
LIST_FIELDS = ('name', 'size_gb')
SAVE_ON_TOP = True
UNICODE_FORMAT = '{} ({} GB)'


class DiskOfferingTestCase(TestCase):

    def setUp(self):
        # to avoid caching, clear it before tests
        cache.clear()
        self.admin = DiskOfferingAdmin(DiskOffering, admin.sites.AdminSite())

    def test_search_fields(self):
        self.assertEqual(SEARCH_FIELDS, self.admin.search_fields)

    def test_list_fields(self):
        self.assertEqual(LIST_FIELDS, self.admin.list_display)

    def test_save_position(self):
        self.assertEqual(SAVE_ON_TOP, self.admin.save_on_top)

    def test_adding_gb_to_kb(self):
        disk_offering_form = DiskOfferingForm(
            data={'name': 'disk_offering_small', 'size_gb': 0.5}
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
            data={'name': disk_offering.name, 'size_gb': 1.5},
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

    def test_min_gb_disk_size(self):
        disk_offering_form = DiskOfferingForm(
            data={'name': 'disk_offering_small', 'size_gb': 0.1}
        )
        self.assertTrue(disk_offering_form.is_valid())

        disk_offering_form = DiskOfferingForm(
            data={'name': 'disk_offering_small', 'size_gb': 0.09}
        )
        self.assertFalse(disk_offering_form.is_valid())

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
        disk_factory = DiskOfferingFactory()
        self.assertEqual(
            UNICODE_FORMAT.format(disk_factory.name, disk_factory.size_gb()),
            str(disk_factory)
        )

        disk_offering = DiskOffering()
        self.assertEqual(
            UNICODE_FORMAT.format(disk_offering.name, disk_offering.size_gb()),
            str(disk_offering)
        )

    def test_disk_offering_is_in_admin(self):
        self.assertIn(DiskOffering, admin.site._registry)
        admin_class = admin.site._registry[DiskOffering]
        self.assertIsInstance(admin_class, DiskOfferingAdmin)
