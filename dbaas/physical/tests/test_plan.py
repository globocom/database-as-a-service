# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from unittest import skipIf
from django.test import TestCase
from django.contrib import admin
from physical.admin.plan import PlanAdmin
from physical.models import Plan
from .factory import PlanFactory, EngineFactory, EngineTypeFactory, \
    EnvironmentFactory


SEARCH_FIELDS = ["name"]
LIST_FILTER = (
    "is_active", "engine", "environments", "is_ha", "has_persistence"
)
LIST_FIELDS = (
    "name", "engine", "environment", "is_active", "provider", "is_ha"
)
SAVE_ON_TOP = True

def _have_cloud_stack():
    import imp
    try:
        imp.find_module('dbaas_cloudstack')
    except ImportError:
        return False
    else:
        return True


class PlanTestCase(TestCase):

    def setUp(self):
        self.admin = PlanAdmin(Plan, admin.sites.AdminSite())

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

        engines = self.admin._get_engines_type()
        self.assertIsInstance(engines, dict)
        self.assertIn(engine_disk, engines)
        self.assertFalse(engines[engine_disk])
        self.assertIn(engine_memory, engines)
        self.assertTrue(engines[engine_memory])


class PlanModelTestCase(TestCase):

    def setUp(self):
        self.plan = PlanFactory()
        self.environment = EnvironmentFactory()
        self.plan.environments.add(self.environment)
        self.plan.environments.add(EnvironmentFactory())

    def test_is_pre_provisioned(self):
        self.plan.provider = Plan.PREPROVISIONED
        self.assertTrue(self.plan.is_pre_provisioned)

        self.plan.provider = Plan.CLOUDSTACK
        self.assertFalse(self.plan.is_pre_provisioned)

    def test_is_cloudstack(self):
        self.plan.provider = Plan.CLOUDSTACK
        self.assertTrue(self.plan.is_cloudstack)

        self.plan.provider = Plan.PREPROVISIONED
        self.assertFalse(self.plan.is_cloudstack)

    def test_migrate_to(self):
        plan = PlanFactory()
        plan_dest_1 = PlanFactory()
        plan_dest_2 = PlanFactory()

        plan_dest_1.migrate_plan = plan
        plan_dest_1.save()

        plan_dest_2.migrate_plan = plan
        plan_dest_2.save()

        migrate_to = plan.migrate_to.all()
        self.assertEqual(len(migrate_to), 2)
        self.assertIn(plan_dest_1, migrate_to)
        self.assertIn(plan_dest_2, migrate_to)

    def test_min_bundles_not_ha(self):
        self.plan.is_ha = False

        self.plan.provider = Plan.PREPROVISIONED
        self.assertTrue(self.plan.validate_min_environment_bundles(
            self.environment
        ))

        self.plan.provider = Plan.CLOUDSTACK
        self.assertTrue(self.plan.validate_min_environment_bundles(
            self.environment
        ))

    @skipIf(not _have_cloud_stack(), "Cloudstack is not installed")
    def test_min_bundles_not_cloudstack(self):
        self.plan.provider = Plan.PREPROVISIONED

        self.plan.is_ha = True
        self.assertTrue(self.plan.validate_min_environment_bundles(
            self.environment
        ))

        self.plan.is_ha = False
        self.assertTrue(self.plan.validate_min_environment_bundles(
            self.environment
        ))
