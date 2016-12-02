# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.test import TestCase
from django.contrib import admin
from physical.admin.plan import PlanAdmin
from physical.models import Plan
from .factory import PlanFactory, EngineFactory, EngineTypeFactory


SEARCH_FIELDS = ["name"]
LIST_FILTER = ("is_active", "engine", "environments", "is_ha")
LIST_FIELDS = (
    "name", "engine", "environment", "is_active", "is_default",
    "provider", "is_ha"
)
SAVE_ON_TOP = True


class PlanTestCase(TestCase):

    def setUp(self):
        self.admin = PlanAdmin(Plan, admin.sites.AdminSite())

    def test_there_can_be_only_one_default_plan(self):
        """
        Highlander test
        """

        plan = PlanFactory()

        self.assertTrue(plan.is_default)

        plan_2 = PlanFactory()

        self.assertTrue(plan_2.is_default)

        plan = Plan.objects.get(id=plan.id)
        self.assertFalse(plan.is_default)

        default_plans = Plan.objects.filter(
            is_default=True, engine=plan_2.engine)
        self.assertEqual(default_plans.count(), 1)

    def test_search_fields(self):
        self.assertEqual(SEARCH_FIELDS, self.admin.search_fields)

    def test_list_filters(self):
        self.assertEqual(LIST_FILTER, self.admin.list_filter)

    def test_list_fields(self):
        self.assertEqual(LIST_FIELDS, self.admin.list_display)

    def test_save_position(self):
        self.assertEqual(SAVE_ON_TOP, self.admin.save_on_top)

    def test_add_extra_context(self):
        context = {'fake': 'test'}
        context = self.admin.add_extra_context(context=context)
        self.assertIn('fake', context)
        self.assertIn('replication_topologies_engines', context)
        self.assertIn('engines', context)

    def test_add_extra_context_without_context(self):
        context = self.admin.add_extra_context(context=None)
        self.assertIsNotNone(context)
        self.assertIsInstance(context, dict)

    def test_get_engine_type(self):
        engine_type_in_memory = EngineTypeFactory()
        engine_type_in_memory.name = 'redis'
        engine_type_in_memory.is_in_memory = True
        engine_type_in_memory.save()

        engine_memory = EngineFactory()
        engine_memory.version = 'in_memory'
        engine_memory.engine_type = engine_type_in_memory
        engine_memory.save()

        engine_disk = EngineFactory()
        engine_disk.version = 'in_disk'
        engine_disk.save()

        import pdb; pdb.set_trace()

        engines = self.admin._get_engines_type()
        self.assertIsInstance(engines, dict)
        self.assertIn(engine_disk, engines)
        self.assertFalse(engines[engine_disk])
        self.assertIn(engine_memory, engines)
        self.assertTrue(engines[engine_memory])
