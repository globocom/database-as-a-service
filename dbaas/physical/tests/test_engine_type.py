# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.test import TestCase
from django.contrib import admin
from physical.admin.engine_type import EngineTypeAdmin
from physical.models import EngineType


SEARCH_FIELDS = ('name', )
LIST_FILTER = ('is_in_memory', )
LIST_FIELDS = ('name', 'is_in_memory', 'created_at')
SAVE_ON_TOP = True


class EngineTypeTestCase(TestCase):

    def setUp(self):
        self.admin = EngineTypeAdmin(EngineType, admin.sites.AdminSite())

    def test_search_fields(self):
        self.assertEqual(SEARCH_FIELDS, self.admin.search_fields)

    def test_list_filters(self):
        self.assertEqual(LIST_FILTER, self.admin.list_filter)

    def test_list_fields(self):
        self.assertEqual(LIST_FIELDS, self.admin.list_display)

    def test_save_position(self):
        self.assertEqual(SAVE_ON_TOP, self.admin.save_on_top)
